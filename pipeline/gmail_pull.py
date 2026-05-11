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
        thread = service.users().threads().get(userId="me", id=tid, format="metadata",
                                                metadataHeaders=["Subject", "From", "Date"]).execute()
        stubs.extend(_process_thread(thread, domains))
    return stubs


def _process_thread(thread: dict, domains: dict) -> list[VaultFile]:
    messages = thread.get("messages", [])
    if not messages:
        return []
    headers = {h["name"]: h["value"] for h in messages[0].get("payload", {}).get("headers", [])}
    sender = headers.get("From", "")
    subject = headers.get("Subject", "(no subject)")
    date_raw = headers.get("Date", "")

    email_addr = re.search(r"<(.+?)>", sender)
    email_addr = email_addr.group(1) if email_addr else sender

    customer_info = match_domain(email_addr, domains)
    if not customer_info:
        return []

    body_text = _extract_body(messages[0])
    is_t2 = flag_tier2(subject + " " + body_text)
    date_str = _parse_email_date(date_raw)

    stub = build_email_stub(
        customer_name=customer_info["customer"],
        product=customer_info["product"],
        subject=subject,
        sender=sender,
        date_str=date_str,
        thread_id=thread["id"],
        is_tier2=is_t2,
    )
    return [stub]


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
    path = f"Entropy/{product}/{customer_name}/Emails/{date_str}_{safe_subject}.md"
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


def _extract_body(message: dict) -> str:
    try:
        data = message["payload"]["body"].get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    except (KeyError, ValueError):
        pass
    return ""


def _parse_email_date(raw: str) -> str:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d")
