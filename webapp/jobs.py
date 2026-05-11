# webapp/jobs.py
import json
import threading
import uuid
from datetime import datetime, timezone

from pipeline import ingest, kimi, notion_pull, gmail_pull, readai_pull, vault_builder
from pipeline.models import JobConfig
from . import s3

_STEPS = ["ingest", "wiki", "gaps", "notion", "gmail", "readai", "assembly"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _update_state(job_id: str, **kwargs) -> None:
    """Update job state in S3. Never include credential fields (tokens, API keys)."""
    state = s3.read_job_state(job_id) or {}
    state.update(kwargs)
    state["updated_at"] = _now()
    s3.write_job_state(job_id, state)


def create_job(config_dict: dict, s3_keys: list[str]) -> str:
    job_id = str(uuid.uuid4())
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
        "created_at": _now(),
        "updated_at": _now(),
    }
    s3.write_job_state(job_id, state)
    t = threading.Thread(
        target=run_pipeline_job,
        args=(job_id, config_dict, s3_keys),
        daemon=True,
    )
    t.start()
    return job_id


def run_pipeline_job(job_id: str, config_dict: dict, s3_keys: list[str]) -> None:
    try:
        config = JobConfig(**config_dict)

        _update_state(job_id, status="processing", step="ingest", step_index=0)
        sources = _download_s3_files(s3_keys)
        ingested = ingest.ingest(sources)

        _update_state(job_id, step="wiki", step_index=1)
        wiki_files = kimi.generate_wiki(config, ingested)

        _update_state(job_id, step="gaps", step_index=2)
        gap_items = kimi.analyze_gaps(config, wiki_files)
        _update_state(job_id, gaps=[
            {"category": g.category, "description": g.description,
             "prompt": g.prompt, "upload_accepted": g.upload_accepted}
            for g in gap_items
        ])

        _update_state(job_id, step="notion", step_index=3)
        customers = notion_pull.pull_customers(config)
        config.product_lines = list({c.product for c in customers})
        customer_files = [notion_pull.build_intelligence_summary(c) for c in customers]
        domains_vf = notion_pull.build_customer_domains(customers)
        hub_nodes = notion_pull.build_hub_nodes(customers)
        domains = json.loads(domains_vf.content)

        _update_state(job_id, step="gmail", step_index=4)
        email_files = gmail_pull.pull_emails(config, domains)

        _update_state(job_id, step="readai", step_index=5)
        transcript_files = readai_pull.pull_transcripts(config, domains)

        _update_state(job_id, step="assembly", step_index=6)
        all_customer_files = customer_files + [domains_vf] + email_files + transcript_files
        zip_bytes = vault_builder.build_vault(
            config, wiki_files, customers, all_customer_files, hub_nodes, gap_items
        )
        vault_key = s3.upload_vault(job_id, zip_bytes)
        claude_settings_key = s3.upload_claude_settings(job_id, generate_claude_settings(config))

        _update_state(
            job_id,
            status="complete",
            step="complete",
            step_index=7,
            vault_key=vault_key,
            claude_settings_key=claude_settings_key,
        )
    except Exception as exc:
        _update_state(job_id, status="error", error=str(exc))


def _download_s3_files(s3_keys: list[str]) -> list[dict]:
    from .s3 import _client
    from .config import settings as s3_settings
    sources = []
    client = _client()
    for key in s3_keys:
        obj = client.get_object(Bucket=s3_settings.s3_bucket, Key=key)
        content = obj["Body"].read()
        filename = key.rsplit("/", 1)[-1]
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "zip":
            sources.append({"type": "zip", "content": content})
        elif ext == "opml":
            sources.append({"type": "opml", "content": content})
        else:
            sources.append({"type": "file", "content": content, "filename": filename})
    return sources


def generate_claude_settings(config: JobConfig) -> str:
    google = config.google_credentials or {}
    return json.dumps({
        "mcpServers": {
            "notion": {
                "command": "npx",
                "args": ["-y", "@notionhq/notion-mcp-server"],
                "env": {
                    "NOTION_API_KEY": config.notion_token,
                    "OPENAPI_MCP_HEADERS": json.dumps({
                        "Authorization": f"Bearer {config.notion_token}",
                        "Notion-Version": "2022-06-28",
                    }),
                }
            },
            "gmail": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-gmail"],
                "env": {
                    "GMAIL_ACCESS_TOKEN": google.get("access_token", ""),
                    "GMAIL_REFRESH_TOKEN": google.get("refresh_token", ""),
                    "GMAIL_CLIENT_ID": google.get("client_id", ""),
                    "GMAIL_CLIENT_SECRET": google.get("client_secret", ""),
                }
            },
            "readai": {
                "command": "npx",
                "args": ["-y", "@read-ai/mcp-server"],
                "env": {
                    "READAI_API_KEY": config.readai_api_key,
                }
            },
        }
    }, indent=2)
