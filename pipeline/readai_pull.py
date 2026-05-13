# entropy_builder/pipeline/readai_pull.py
import re
import requests
from datetime import datetime, timedelta, timezone
from .models import JobConfig, VaultFile

READAI_BASE = "https://api.read.ai/v1"
_READAI_TOKEN_URL = "https://authn.read.ai/oauth2/token"


def _refresh_access_token(config: JobConfig) -> str:
    """Return a fresh access token using the refresh token. Falls back to the stored token on failure."""
    if not config.readai_refresh_token or not config.readai_client_id:
        return config.readai_access_token
    try:
        resp = requests.post(_READAI_TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": config.readai_refresh_token,
            "client_id": config.readai_client_id,
        }, timeout=15)
        resp.raise_for_status()
        return resp.json().get("access_token", config.readai_access_token)
    except Exception:
        return config.readai_access_token


def pull_transcripts(config: JobConfig, domains: dict) -> list[VaultFile]:
    """Pull last 90 days of read.ai meetings and match to customers."""
    cutoff_ms = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000)
    access_token = _refresh_access_token(config)
    headers = {"Authorization": f"Bearer {access_token}"}

    meetings = []
    cursor = None
    while True:
        params = [
            ("limit", 10),
            ("start_time_ms.gte", cutoff_ms),
            ("expand[]", "summary"),
            ("expand[]", "action_items"),
        ]
        if cursor:
            params.append(("cursor", cursor))
        resp = requests.get(f"{READAI_BASE}/meetings", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        page = data.get("data", [])
        meetings.extend(page)
        if len(meetings) >= 200 or not data.get("has_more") or not page:
            break
        cursor = page[-1]["id"]

    meetings = meetings[:200]
    stubs = []
    for meeting in meetings:
        customer_info = match_meeting_to_customer(meeting, domains)
        if not customer_info:
            continue
        start_ms = meeting.get("start_time_ms", 0)
        date_str = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        stub = build_transcript_stub(
            customer_name=customer_info["customer"],
            product=customer_info["product"],
            title=meeting.get("title", "Meeting"),
            date_str=date_str,
            meeting_id=meeting.get("id", "unknown"),
            summary=meeting.get("summary", ""),
            action_items=meeting.get("action_items", []),
        )
        stubs.append(stub)
    return stubs


def match_meeting_to_customer(meeting: dict, domains: dict) -> dict | None:
    for participant in meeting.get("participants", []):
        email = participant.get("email", "")
        if "@" not in email:
            continue
        domain = email.split("@")[1].lower()
        info = domains.get("domains", {}).get(domain)
        if info:
            return info
    return None


def build_transcript_stub(customer_name: str, product: str, title: str,
                           date_str: str, meeting_id: str, summary: str,
                           action_items: list | None = None) -> VaultFile:
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "-")[:50]
    path = f"Entropy/{product}/{customer_name}/Transcripts/{date_str}_{safe_title}.md"

    action_items_text = "_Pending — run debrief skill_"
    if action_items:
        lines = []
        for item in action_items:
            text = item.get("text") or item.get("description") or str(item)
            assignee = item.get("assignee") or item.get("owner") or ""
            due = item.get("due_date") or item.get("due") or ""
            line = f"- {text}"
            if assignee:
                line += f" ({assignee})"
            if due:
                line += f" — due {due}"
            lines.append(line)
        action_items_text = "\n".join(lines)

    content = f"""---
type: transcript
customer: "{customer_name}"
product: "{product}"
date: "{date_str}"
meeting_id: "{meeting_id}"
source: read.ai
tags: [transcript, {product.lower()}]
---

# {title}

**Date:** {date_str}
**Meeting ID:** {meeting_id}

## Summary

{summary or "_[Auto-ingested stub — run debrief skill to extract full summary]_"}

## Action Items

{action_items_text}

## Key Signals

_Pending — run debrief skill_
"""
    return VaultFile(path=path, content=content)
