# webapp/jobs.py
import json
import time
import uuid
from datetime import datetime, timezone

import boto3

from pipeline import ingest, kimi, notion_pull, gmail_pull, readai_pull, vault_builder
from pipeline.models import JobConfig
from . import s3
from .config import settings as _webapp_settings

_STEPS = ["ingest", "wiki", "gaps", "notion", "gmail", "readai", "assembly"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _update_state(job_id: str, **kwargs) -> None:
    """Update job state in S3. Never include credential fields (tokens, API keys)."""
    state = s3.read_job_state(job_id) or {}
    state.update(kwargs)
    state["updated_at"] = _now()
    s3.write_job_state(job_id, state)


def update_job_state(job_id: str, **kwargs) -> None:
    """Public wrapper around _update_state for use outside this module."""
    _update_state(job_id, **kwargs)


def log_activity(job_id: str, message: str, kind: str = "info", tokens: int | None = None) -> None:
    """Append one row to the job's activity log (capped at 50 entries)."""
    state = s3.read_job_state(job_id) or {}
    log = state.get("activity_log", [])
    entry: dict = {"ts": int(time.time()), "kind": kind, "message": message}
    if tokens is not None:
        entry["tokens"] = tokens
    log.append(entry)
    log = log[-50:]
    _update_state(job_id, activity_log=log)


def set_current_activity(
    job_id: str,
    file: str | None,
    kind: str = "file",
    index: int | None = None,
    total: int | None = None,
    tokens: int | None = None,
) -> None:
    """Set the live 'currently processing' line. Pass file=None to clear it."""
    if file is None:
        _update_state(job_id, current_activity=None)
        return
    activity: dict = {"file": file, "kind": kind}
    if index is not None:
        activity["index"] = index
    if total is not None:
        activity["total"] = total
    if tokens is not None:
        activity["tokens"] = tokens
    _update_state(job_id, current_activity=activity)


def create_job(config_dict: dict, s3_keys: list[str], owner_sub: str = "") -> str:
    job_id = str(uuid.uuid4())
    s3.write_job_config(job_id, config_dict)
    state = {
        "job_id": job_id,
        "status": "pending",
        "step": "ingest",
        "step_index": 0,
        "total_steps": len(_STEPS),
        "gaps": [],
        "gap_s3_keys": [],
        "vault_key": None,
        "claude_settings_key": None,
        "error": None,
        "owner_sub": owner_sub,
        "created_at": _now(),
        "updated_at": _now(),
    }
    s3.write_job_state(job_id, state)
    sqs = boto3.client("sqs", region_name=_webapp_settings.aws_region)
    sqs.send_message(
        QueueUrl=_webapp_settings.sqs_queue_url,
        MessageBody=json.dumps({"job_id": job_id, "s3_keys": s3_keys}),
    )
    return job_id


def run_pipeline_job(job_id: str, config_dict: dict, s3_keys: list[str]) -> None:
    try:
        config = JobConfig(**config_dict)
        tokens_total = [0]

        # --- Ingest ---
        _update_state(job_id,
                      status="processing", step="ingest", step_index=0,
                      started_at=int(time.time()), tokens_total=0,
                      activity_log=[], current_activity=None)
        log_activity(job_id, "Job started", kind="phase")
        log_activity(job_id, "Ingesting uploaded files", kind="phase")

        sources = []
        for i, key in enumerate(s3_keys):
            name = key.rsplit("/", 1)[-1]
            set_current_activity(job_id, name, kind="file",
                                 index=i + 1, total=len(s3_keys) or 1)
            log_activity(job_id, f"Reading {name}", kind="file")
            sources.append(_download_one_s3_file(key))

        set_current_activity(job_id, None)
        ingested = ingest.ingest(sources)
        log_activity(job_id, f"Ingested {len(ingested)} file(s)", kind="info")

        # --- Wiki ---
        _update_state(job_id, step="wiki", step_index=1)
        log_activity(job_id, "Building knowledge wiki", kind="phase")

        def _on_wiki_chunk(chunk_idx: int, total_chunks: int, tokens: int) -> None:
            tokens_total[0] += tokens
            label = f"chunk {chunk_idx} of {total_chunks}" if total_chunks > 1 else "synthesis"
            set_current_activity(job_id, label, kind="synthesize",
                                 index=chunk_idx, total=total_chunks)
            log_activity(job_id, f"Synthesized {label}", kind="synthesize")
            if tokens:
                log_activity(job_id, "", kind="tokens", tokens=tokens)
            # Update ETA: elapsed / chunks_done * remaining
            state = s3.read_job_state(job_id) or {}
            started = state.get("started_at", int(time.time()))
            elapsed = time.time() - started
            chunks_remaining = total_chunks - chunk_idx
            eta = int((elapsed / chunk_idx) * chunks_remaining) if chunk_idx else 0
            _update_state(job_id, tokens_total=tokens_total[0], eta_seconds=eta)

        wiki_files = kimi.generate_wiki(config, ingested, on_chunk=_on_wiki_chunk)
        set_current_activity(job_id, None)
        log_activity(job_id, f"Wiki built: {len(wiki_files)} file(s)", kind="info")

        # --- Gaps ---
        _update_state(job_id, step="gaps", step_index=2)
        log_activity(job_id, "Analyzing knowledge gaps", kind="phase")
        set_current_activity(job_id, "gap analysis", kind="synthesize")
        gap_items = kimi.analyze_gaps(config, wiki_files)
        set_current_activity(job_id, None)
        _update_state(job_id, gaps=[
            {"category": g.category, "description": g.description,
             "prompt": g.prompt, "upload_accepted": g.upload_accepted}
            for g in gap_items
        ])
        log_activity(job_id, f"Found {len(gap_items)} gap(s)", kind="info")

        # --- Notion ---
        _update_state(job_id, step="notion", step_index=3)
        log_activity(job_id, "Importing Notion customer data", kind="phase")
        set_current_activity(job_id, "Notion database", kind="notion")
        customers = notion_pull.pull_customers(config)
        config.product_lines = list({c.product for c in customers})
        customer_files = [notion_pull.build_intelligence_summary(c) for c in customers]
        domains_vf = notion_pull.build_customer_domains(customers)
        hub_nodes = notion_pull.build_hub_nodes(customers)
        domains = json.loads(domains_vf.content)
        set_current_activity(job_id, None)
        log_activity(job_id, f"Imported {len(customers)} customer(s)", kind="info")

        # --- Gmail ---
        _update_state(job_id, step="gmail", step_index=4)
        log_activity(job_id, "Pulling Gmail history", kind="phase")
        set_current_activity(job_id, "Gmail inbox", kind="gmail")
        try:
            email_files = gmail_pull.pull_emails(config, domains)
            log_activity(job_id, f"Fetched {len(email_files)} email thread(s)", kind="info")
        except Exception as exc:
            email_files = []
            log_activity(job_id, f"Gmail skipped: {exc}", kind="error")
        set_current_activity(job_id, None)

        # --- read.ai ---
        _update_state(job_id, step="readai", step_index=5)
        log_activity(job_id, "Pulling read.ai transcripts", kind="phase")
        set_current_activity(job_id, "read.ai", kind="file")
        try:
            transcript_files = readai_pull.pull_transcripts(config, domains)
            log_activity(job_id, f"Fetched {len(transcript_files)} transcript(s)", kind="info")
        except Exception as exc:
            transcript_files = []
            log_activity(job_id, f"read.ai skipped: {exc}", kind="error")
        set_current_activity(job_id, None)

        # --- Assembly ---
        _update_state(job_id, step="assembly", step_index=6)
        log_activity(job_id, "Assembling vault", kind="phase")
        set_current_activity(job_id, "building zip", kind="synthesize")
        all_customer_files = customer_files + [domains_vf] + email_files + transcript_files
        zip_bytes = vault_builder.build_vault(
            config, wiki_files, customers, all_customer_files, hub_nodes, gap_items
        )
        vault_key = s3.upload_vault(job_id, zip_bytes)
        claude_settings_key = s3.upload_claude_settings(job_id, generate_claude_settings(config))
        set_current_activity(job_id, None)

        _update_state(
            job_id,
            status="complete",
            step="complete",
            step_index=7,
            vault_key=vault_key,
            claude_settings_key=claude_settings_key,
            eta_seconds=0,
        )
        log_activity(job_id, "Vault complete", kind="phase")
    except Exception as exc:
        try:
            _update_state(job_id, status="error", error=str(exc))
            log_activity(job_id, str(exc), kind="error")
        except Exception:
            pass  # S3 unreachable — job stays in last known state
        raise  # let the worker decide whether to retry via SQS


def _download_one_s3_file(key: str) -> dict:
    from .s3 import _client
    from .config import settings as s3_settings
    obj = _client().get_object(Bucket=s3_settings.s3_bucket, Key=key)
    content = obj["Body"].read()
    filename = key.rsplit("/", 1)[-1]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "zip":
        return {"type": "zip", "content": content}
    if ext == "opml":
        return {"type": "opml", "content": content}
    return {"type": "file", "content": content, "filename": filename}


def _download_s3_files(s3_keys: list[str]) -> list[dict]:
    return [_download_one_s3_file(key) for key in s3_keys]


def generate_claude_settings(config: JobConfig) -> str:
    google = config.google_credentials or {}
    return json.dumps({
        "mcpServers": {
            "gmail": {
                "command": "npx",
                "args": ["-y", _webapp_settings.gmail_mcp_package],
                "env": {
                    "GMAIL_ACCESS_TOKEN": google.get("access_token", ""),
                    "GMAIL_REFRESH_TOKEN": google.get("refresh_token", ""),
                    "GMAIL_CLIENT_ID": google.get("client_id", ""),
                    "GMAIL_CLIENT_SECRET": google.get("client_secret", ""),
                }
            },
            "readai": {
                "command": "npx",
                "args": ["-y", _webapp_settings.readai_mcp_package],
                "env": {
                    "READAI_API_KEY": config.readai_api_key,
                }
            },
        }
    }, indent=2)
