# entropy_builder/pipeline/readai_pull.py
import re
import requests
from datetime import datetime, timedelta, timezone
from .models import JobConfig, VaultFile

READAI_BASE = "https://api.read.ai/v1"


def pull_transcripts(config: JobConfig, domains: dict) -> list[VaultFile]:
    """Pull last 90 days of read.ai meetings and match to customers."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    headers = {"Authorization": f"Bearer {config.readai_api_key}"}

    meetings = []
    page_token = None
    while True:
        params = {"after": cutoff, "limit": 50}
        if page_token:
            params["page_token"] = page_token
        resp = requests.get(f"{READAI_BASE}/meetings", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        meetings.extend(data.get("meetings", []))
        if len(meetings) > 200:
            meetings = meetings[:200]
        page_token = data.get("next_page_token")
        if not page_token or len(meetings) >= 200:
            break

    stubs = []
    for meeting in meetings:
        customer_info = match_meeting_to_customer(meeting, domains)
        if not customer_info:
            continue
        date_str = meeting.get("date", "")[:10]
        stub = build_transcript_stub(
            customer_name=customer_info["customer"],
            product=customer_info["product"],
            title=meeting.get("title", "Meeting"),
            date_str=date_str,
            meeting_id=meeting.get("id", "unknown"),
            summary=meeting.get("summary", ""),
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
                           date_str: str, meeting_id: str, summary: str) -> VaultFile:
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "-")[:50]
    path = f"Entropy/{product}/{customer_name}/Transcripts/{date_str}_{safe_title}.md"
    content = f"""---
customer: "{customer_name}"
product: "{product}"
date: "{date_str}"
meeting_id: "{meeting_id}"
tags: [transcript, {product.lower()}]
---

# {title}

**Date:** {date_str}
**Meeting ID:** {meeting_id}

## Summary

{summary or "_[Auto-ingested stub — run debrief skill to extract full summary]_"}

## Action Items

_Pending analysis_

## Key Signals

_Pending analysis_
"""
    return VaultFile(path=path, content=content)
