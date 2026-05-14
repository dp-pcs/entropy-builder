# entropy_builder/pipeline/gmail_pull.py
import base64
import json
import re
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .models import JobConfig, VaultFile

TIER2_KEYWORDS = [
    "cancel", "terminate", "alternative", "considering options",
    "competitor", "budget cut", "unacceptable", "executive review",
    "not renewing", "looking elsewhere", "switching",
]

# Senders on these domains are the user's own org — never a customer match.
# Per Entropy _skills/ingestion.md role-classification table.
INTERNAL_DOMAINS = {"trilogy.com", "aurea.com", "skyvera.com"}

# Reseller domains route to many customers; preserve the thread but flag for
# subject/body disambiguation downstream (per _skills/ingestion.md:150).
RESELLER_DOMAINS = {
    "shi.com", "carahsoft.com", "bechtle.com", "softwareone.com",
    "penril.net", "tekservinc.com",
}


def _extract_email_addr(from_header: str) -> str:
    m = re.search(r"<(.+?)>", from_header)
    return (m.group(1) if m else from_header).strip()


def pull_emails(config: JobConfig, domains: dict) -> list[VaultFile]:
    """Pull last 90 days of Gmail and match to customers via domains dict."""
    creds = Credentials(
        token=config.google_credentials["access_token"],
        refresh_token=config.google_credentials.get("refresh_token"),
        client_id=config.google_credentials.get("client_id"),
        client_secret=config.google_credentials.get("client_secret"),
        token_uri=config.google_credentials.get("token_uri", "https://oauth2.googleapis.com/token"),
    )
    service = build("gmail", "v1", credentials=creds)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y/%m/%d")
    query = f"after:{cutoff}"

    thread_ids = []
    page_token = None
    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.users().threads().list(**kwargs).execute()
        thread_ids.extend(t["id"] for t in resp.get("threads", []))
        thread_ids = thread_ids[:500]
        page_token = resp.get("nextPageToken")
        if not page_token or len(thread_ids) >= 500:
            break

    stubs = []
    for tid in thread_ids:
        # format="full" — needed so _extract_body can read message bodies for
        # Tier-2 keyword detection. format="metadata" returns headers only and
        # silently empties the body, making body-based Tier-2 a no-op.
        thread = service.users().threads().get(userId="me", id=tid, format="full").execute()
        stubs.extend(_process_thread(thread, domains))
    return stubs


def _thread_text_for_tier2(messages: list) -> str:
    """Concatenate every subject + snippet + body across a thread for keyword scan."""
    parts = []
    for msg in messages:
        payload = msg.get("payload", {}) or {}
        for h in payload.get("headers", []) or []:
            if h.get("name") == "Subject":
                parts.append(h.get("value", ""))
        snippet = msg.get("snippet")
        if snippet:
            parts.append(snippet)
        body = _extract_body(msg)
        if body:
            parts.append(body)
    return " ".join(parts)


def _process_thread(thread: dict, domains: dict) -> list[VaultFile]:
    messages = thread.get("messages", [])
    if not messages:
        return []

    # Walk every message in the thread — not just messages[0]. The user often
    # initiates threads to customers, so the first sender is internal and the
    # real customer signal is in later replies.
    customer_info = None
    reseller_domain = None
    for msg in messages:
        msg_headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        email_addr = _extract_email_addr(msg_headers.get("From", ""))
        if "@" not in email_addr:
            continue
        domain = email_addr.split("@")[1].lower()
        if domain in INTERNAL_DOMAINS:
            continue
        if domain in RESELLER_DOMAINS:
            reseller_domain = reseller_domain or domain
            continue
        info = domains.get("domains", {}).get(domain)
        if info:
            customer_info = info
            break

    first = {h["name"]: h["value"] for h in messages[0].get("payload", {}).get("headers", [])}
    sender = first.get("From", "")
    subject = first.get("Subject", "(no subject)")
    date_str = _parse_email_date(first.get("Date", ""))
    is_t2 = flag_tier2(_thread_text_for_tier2(messages))

    if customer_info:
        return [build_email_stub(
            customer_name=customer_info["customer"],
            product=customer_info["product"],
            subject=subject,
            sender=sender,
            date_str=date_str,
            thread_id=thread["id"],
            is_tier2=is_t2,
        )]

    if reseller_domain:
        return [build_reseller_stub(
            reseller_domain=reseller_domain,
            subject=subject,
            sender=sender,
            date_str=date_str,
            thread_id=thread["id"],
            is_tier2=is_t2,
        )]

    return []


def pull_general_emails(config: JobConfig) -> list[VaultFile]:
    """Pull last 90 days of Gmail for non-PM users — broad scan, no domain filtering."""
    creds = Credentials(
        token=config.google_credentials["access_token"],
        refresh_token=config.google_credentials.get("refresh_token"),
        client_id=config.google_credentials.get("client_id"),
        client_secret=config.google_credentials.get("client_secret"),
        token_uri=config.google_credentials.get("token_uri", "https://oauth2.googleapis.com/token"),
    )
    service = build("gmail", "v1", credentials=creds)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y/%m/%d")
    # Exclude bulk/automated mail; focus on real human threads
    query = (
        f"after:{cutoff} "
        "-category:promotions -category:social -category:updates -category:forums "
        "-from:noreply -from:no-reply -from:donotreply"
    )

    thread_ids = []
    page_token = None
    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.users().threads().list(**kwargs).execute()
        thread_ids.extend(t["id"] for t in resp.get("threads", []))
        thread_ids = thread_ids[:300]
        page_token = resp.get("nextPageToken")
        if not page_token or len(thread_ids) >= 300:
            break

    stubs = []
    for tid in thread_ids:
        thread = service.users().threads().get(userId="me", id=tid, format="metadata",
                                                metadataHeaders=["Subject", "From", "Date"]).execute()
        stub = _process_general_thread(thread)
        if stub:
            stubs.append(stub)
    return stubs


def _process_general_thread(thread: dict) -> VaultFile | None:
    messages = thread.get("messages", [])
    if not messages:
        return None
    headers = {h["name"]: h["value"] for h in messages[0].get("payload", {}).get("headers", [])}
    sender = headers.get("From", "")
    subject = headers.get("Subject", "(no subject)")
    date_raw = headers.get("Date", "")

    email_addr = _extract_email_addr(sender)

    # Skip obvious automated senders
    automated = ["noreply", "no-reply", "donotreply", "notifications@", "alerts@", "mailer-daemon"]
    if any(x in email_addr.lower() for x in automated):
        return None

    sender_name_match = re.search(r"^(.+?)\s*<", sender)
    sender_name = sender_name_match.group(1).strip().strip('"') if sender_name_match else email_addr.split("@")[0]

    date_str = _parse_email_date(date_raw)
    safe_sender = re.sub(r"[^\w\s-]", "", sender_name).strip().replace(" ", "-")[:40]
    safe_subject = re.sub(r"[^\w\s-]", "", subject).strip().replace(" ", "-")[:50]
    path = f"Portfolio Brain/Inbox/{safe_sender}/{date_str}_{safe_subject}.md"

    content = f"""---
sender: "{sender}"
date: "{date_str}"
thread_id: "{thread['id']}"
tags: [email, inbox]
---

# {subject}

**From:** {sender}
**Date:** {date_str}

## Summary

_[Auto-ingested — run analysis skill to extract key points]_

## Key Points

_Pending analysis_
"""
    return VaultFile(path=path, content=content)


def match_domain(email: str, domains: dict) -> dict | None:
    if "@" not in email:
        return None
    domain = email.split("@")[1].lower()
    return domains.get("domains", {}).get(domain)


def flag_tier2(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in TIER2_KEYWORDS)


def build_email_stub(customer_name: str, product: str, subject: str,
                     sender: str, date_str: str, thread_id: str, is_tier2: bool) -> VaultFile:
    safe_subject = re.sub(r"[^\w\s-]", "", subject).strip().replace(" ", "-")[:50]
    path = f"Portfolio Brain/{product}/{customer_name}/Emails/{date_str}_{safe_subject}.md"
    tier2_flag = "true" if is_tier2 else "false"
    content = f"""---
customer: "{customer_name}"
product: "{product}"
date: "{date_str}"
thread_id: "{thread_id}"
tier2: {tier2_flag}
tags: [email, {product.lower()}]
---

# {subject}

**From:** {sender}
**Date:** {date_str}
**Thread:** {thread_id}

## Summary

_[Auto-ingested stub — run debrief skill to extract full summary]_

## Key Points

_Pending analysis_
"""
    return VaultFile(path=path, content=content)


def build_reseller_stub(reseller_domain: str, subject: str, sender: str,
                         date_str: str, thread_id: str, is_tier2: bool) -> VaultFile:
    """Preserve threads where the only external sender is a known reseller.

    Resellers map to many customers, so the customer can't be resolved from the
    domain alone. Downstream skills disambiguate via subject/body content
    (see _skills/ingestion.md:150).
    """
    safe_subject = re.sub(r"[^\w\s-]", "", subject).strip().replace(" ", "-")[:50]
    path = f"Portfolio Brain/_inbox/Resellers/{reseller_domain}/{date_str}_{safe_subject}.md"
    tier2_flag = "true" if is_tier2 else "false"
    content = f"""---
ambiguous: true
reseller_domain: "{reseller_domain}"
date: "{date_str}"
thread_id: "{thread_id}"
tier2: {tier2_flag}
tags: [email, reseller, ambiguous]
---

# {subject}

**From:** {sender}
**Date:** {date_str}
**Reseller:** {reseller_domain}

## Customer

_Unresolved — disambiguate via subject/body content. Reseller domain maps to multiple customers._

## Summary

_[Auto-ingested stub — run debrief skill to extract summary and resolve customer]_
"""
    return VaultFile(path=path, content=content)


def _extract_body(message: dict) -> str:
    payload = message.get("payload", {})
    # Simple (non-multipart) body
    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    # Multipart: walk parts for text/plain
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    return ""


def _parse_email_date(raw: str) -> str:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d")
