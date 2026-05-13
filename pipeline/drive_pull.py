import re
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .models import JobConfig, VaultFile


def pull_drive_docs(config: JobConfig) -> list[VaultFile]:
    """Pull recently modified Google Docs from Drive (last 90 days, max 50)."""
    creds = Credentials(
        token=config.google_credentials["access_token"],
        refresh_token=config.google_credentials.get("refresh_token"),
        client_id=config.google_credentials.get("client_id"),
        client_secret=config.google_credentials.get("client_secret"),
        token_uri=config.google_credentials.get("token_uri", "https://oauth2.googleapis.com/token"),
    )
    service = build("drive", "v3", credentials=creds)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    results = service.files().list(
        q=f"mimeType='application/vnd.google-apps.document' and modifiedTime > '{cutoff}' and trashed = false",
        fields="files(id, name, modifiedTime)",
        pageSize=50,
        orderBy="modifiedTime desc",
    ).execute()

    stubs = []
    for f in results.get("files", []):
        try:
            raw = service.files().export(fileId=f["id"], mimeType="text/plain").execute()
            text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
            stubs.append(_build_stub(f["name"], f["modifiedTime"][:10], f["id"], text[:4000]))
        except Exception:
            pass
    return stubs


def _build_stub(name: str, date_str: str, file_id: str, preview: str) -> VaultFile:
    safe = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "-")[:60]
    path = f"Portfolio Brain/Drive/{date_str}_{safe}.md"
    content = f"""---
source: google_drive
file_id: "{file_id}"
date: "{date_str}"
tags: [drive, document]
---

# {name}

**Modified:** {date_str}

## Content

{preview.strip()}
"""
    return VaultFile(path=path, content=content)
