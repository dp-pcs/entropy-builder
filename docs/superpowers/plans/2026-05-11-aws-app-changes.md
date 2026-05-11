# Entropy AWS App Changes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify the entropy-builder codebase to run on ECS Fargate — replacing background threading with SQS job queuing, adding a standalone worker process, removing Notion OAuth in favour of a shared internal token, updating `claude_settings.json` to omit Notion (users connect via Claude Desktop), and adding a Dockerfile for a single deployable image.

**Architecture:** Same FastAPI app; `create_job()` writes config to S3 and enqueues to SQS instead of spawning a thread. A new `worker/` module long-polls SQS and calls `run_pipeline_job()`. Both web and worker run from the same Docker image with different entry-point commands. The entropy vault template is bundled directly into the repo under `entropy-template/`.

**Tech Stack:** Python 3.11, FastAPI, boto3 (SQS + S3), Docker, pytest-mock.

---

## File Map

```
entropy-builder/
├── entropy-template/                  NEW — bundled vault template (skills, analytics, rules)
│   └── Entropy/
│       ├── _skills/                   copied from ~/Documents/GitHub/entropy/Entropy/_skills/
│       ├── _analytics/                copied from ~/Documents/GitHub/entropy/Entropy/_analytics/
│       └── Company-Rules.md           copied from ~/Documents/GitHub/entropy/Entropy/Company-Rules.md
├── Dockerfile                         NEW — single image, web + worker entry points
├── worker/
│   ├── __init__.py                    NEW — empty
│   └── __main__.py                    NEW — SQS long-poll loop
├── webapp/
│   ├── config.py                      MODIFY — add sqs_queue_url, notion_token
│   ├── s3.py                          MODIFY — add write_job_config, read_job_config
│   ├── jobs.py                        MODIFY — SQS enqueue in create_job(), remove threading,
│   │                                            update generate_claude_settings() to remove Notion
│   ├── main.py                        MODIFY — account-managers uses settings.notion_token;
│   │                                            wizard_submit uses settings.notion_token
│   └── templates/
│       ├── wizard.html                MODIFY — remove Notion OAuth step, remove Notion connect button
│       └── status.html                MODIFY — 4-step setup guide (add Notion via Claude Desktop step)
└── tests/webapp/
    ├── test_s3.py                     MODIFY — add tests for write_job_config, read_job_config
    ├── test_jobs.py                   MODIFY — update create_job tests for SQS; update generate_claude_settings test
    └── test_notion_api.py             MODIFY — account-managers uses shared token, no OAuth session
tests/
└── worker/
    ├── __init__.py                    NEW
    └── test_worker.py                 NEW — test SQS poll loop
```

---

## Task 1: Bundle entropy template files

**Files:**
- Create: `entropy-template/Entropy/_skills/` (16 skill files)
- Create: `entropy-template/Entropy/_analytics/` (3 analytics files + CLAUDE.md)
- Create: `entropy-template/Entropy/Company-Rules.md`

No TDD for this task — it is a file copy and commit.

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p entropy-template/Entropy/_skills
mkdir -p entropy-template/Entropy/_analytics
```

- [ ] **Step 2: Copy skill files from the entropy repo**

```bash
cp ~/Documents/GitHub/entropy/Entropy/_skills/triage.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/debrief.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/playbook.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/health.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/ingestion.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/dashboard.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/alerting.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/enrichment.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/commitment-extraction.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/lint.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/renewal-countdown.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/churn-autopsy.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/email-draft.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/segmentation.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/competitive-intel.md entropy-template/Entropy/_skills/
cp ~/Documents/GitHub/entropy/Entropy/_skills/pressure-test.md entropy-template/Entropy/_skills/
```

- [ ] **Step 3: Copy analytics files**

```bash
cp ~/Documents/GitHub/entropy/Entropy/_analytics/metrics.md entropy-template/Entropy/_analytics/
cp ~/Documents/GitHub/entropy/Entropy/_analytics/queries.md entropy-template/Entropy/_analytics/
cp ~/Documents/GitHub/entropy/Entropy/_analytics/schemas.md entropy-template/Entropy/_analytics/
cp ~/Documents/GitHub/entropy/Entropy/_analytics/CLAUDE.md entropy-template/Entropy/_analytics/
```

- [ ] **Step 4: Copy Company-Rules.md**

```bash
cp ~/Documents/GitHub/entropy/Entropy/Company-Rules.md entropy-template/Entropy/
```

- [ ] **Step 5: Verify structure**

```bash
find entropy-template/ -type f | sort
```

Expected: 21 files total (16 skills + 4 analytics + 1 Company-Rules.md).

- [ ] **Step 6: Commit**

```bash
git add entropy-template/
git commit -m "feat: bundle entropy vault template files for Docker image"
```

---

## Task 2: Add Dockerfile

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENTROPY_TEMPLATE_PATH=/app/entropy-template
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The worker overrides CMD via ECS task definition: `["python", "-m", "worker"]`.

- [ ] **Step 2: Verify Docker build succeeds**

```bash
docker build -t entropy-builder:local .
```

Expected: `Successfully built <image-id>` with no errors.

- [ ] **Step 3: Verify web server starts**

```bash
docker run --rm -p 8000:8000 \
  -e S3_BUCKET=dummy \
  -e ENTROPY_TEMPLATE_PATH=/app/entropy-template \
  entropy-builder:local \
  uvicorn webapp.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl -s http://localhost:8000/health
docker stop $(docker ps -q --filter ancestor=entropy-builder:local)
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Add .dockerignore**

```
.venv/
venv/
__pycache__/
*.pyc
.env
.git/
.worktrees/
tests/
docs/
*.zip
input/
```

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Dockerfile for single web+worker image"
```

---

## Task 3: Update config.py — add sqs_queue_url and notion_token

**Files:**
- Modify: `webapp/config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/webapp/test_config.py  (new file)
import os
import importlib


def test_sqs_queue_url_reads_from_env(monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123/entropy-jobs")
    import webapp.config as cfg
    importlib.reload(cfg)
    assert cfg.Settings().sqs_queue_url == "https://sqs.us-east-1.amazonaws.com/123/entropy-jobs"


def test_notion_token_reads_from_env(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "secret_abc123")
    import webapp.config as cfg
    importlib.reload(cfg)
    assert cfg.Settings().notion_token == "secret_abc123"


def test_defaults_to_empty_string():
    import webapp.config as cfg
    s = cfg.Settings()
    # defaults don't crash even when env vars absent
    assert isinstance(s.sqs_queue_url, str)
    assert isinstance(s.notion_token, str)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/webapp/test_config.py -v
```

Expected: `AttributeError: 'Settings' object has no attribute 'sqs_queue_url'`

- [ ] **Step 3: Add fields to config.py**

Replace the contents of `webapp/config.py` with:

```python
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    s3_bucket: str = field(default_factory=lambda: os.environ.get("S3_BUCKET", ""))
    aws_region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    sqs_queue_url: str = field(default_factory=lambda: os.environ.get("SQS_QUEUE_URL", ""))
    notion_token: str = field(default_factory=lambda: os.environ.get("NOTION_TOKEN", ""))
    google_client_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_ID", ""))
    google_client_secret: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLIENT_SECRET", ""))
    notion_client_id: str = field(default_factory=lambda: os.environ.get("NOTION_CLIENT_ID", ""))
    notion_client_secret: str = field(default_factory=lambda: os.environ.get("NOTION_CLIENT_SECRET", ""))
    notion_database_id: str = field(default_factory=lambda: os.environ.get("NOTION_DATABASE_ID", "28485e927d3181c89d6cdd6fd57ea07d"))
    fireworks_api_key: str = field(default_factory=lambda: os.environ.get("FIREWORKS_API_KEY", ""))
    entropy_template_path: str = field(default_factory=lambda: os.environ.get("ENTROPY_TEMPLATE_PATH", ""))
    base_url: str = field(default_factory=lambda: os.environ.get("BASE_URL", "http://localhost:8000"))
    notion_mcp_package: str = field(default_factory=lambda: os.environ.get("NOTION_MCP_PACKAGE", "@notionhq/notion-mcp-server"))
    gmail_mcp_package: str = field(default_factory=lambda: os.environ.get("GMAIL_MCP_PACKAGE", "@modelcontextprotocol/server-gmail"))
    readai_mcp_package: str = field(default_factory=lambda: os.environ.get("READAI_MCP_PACKAGE", "@read-ai/mcp-server"))


settings = Settings()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/pytest tests/webapp/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add webapp/config.py tests/webapp/test_config.py
git commit -m "feat: add sqs_queue_url and notion_token to Settings"
```

---

## Task 4: Add s3.py — write_job_config and read_job_config

**Files:**
- Modify: `webapp/s3.py`
- Modify: `tests/webapp/test_s3.py`

Credentials (Google tokens, read.ai key, Notion token) are written to `jobs/{job_id}/config.json` so the worker can retrieve them. Job state (`state.json`) never contains credentials.

- [ ] **Step 1: Write the failing tests**

Add to `tests/webapp/test_s3.py`:

```python
def test_write_job_config_stores_config(mocker):
    mock_s3 = mocker.MagicMock()
    mocker.patch("webapp.s3._client", return_value=mock_s3)
    mocker.patch("webapp.s3.settings")
    from webapp.s3 import write_job_config
    write_job_config("j1", {"notion_token": "secret", "user_name": "Alice"})
    call_kwargs = mock_s3.put_object.call_args[1]
    import json
    body = json.loads(call_kwargs["Body"])
    assert body["notion_token"] == "secret"
    assert call_kwargs["Key"] == "jobs/j1/config.json"
    assert call_kwargs["ServerSideEncryption"] == "AES256"


def test_read_job_config_returns_dict(mocker):
    import json
    mock_s3 = mocker.MagicMock()
    mock_s3.get_object.return_value = {
        "Body": mocker.MagicMock(read=lambda: json.dumps({"notion_token": "tok"}).encode())
    }
    mocker.patch("webapp.s3._client", return_value=mock_s3)
    mocker.patch("webapp.s3.settings")
    from webapp.s3 import read_job_config
    result = read_job_config("j1")
    assert result["notion_token"] == "tok"


def test_read_job_config_returns_none_when_missing(mocker):
    from botocore.exceptions import ClientError
    mock_s3 = mocker.MagicMock()
    mock_s3.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": ""}}, "GetObject"
    )
    mocker.patch("webapp.s3._client", return_value=mock_s3)
    mocker.patch("webapp.s3.settings")
    from webapp.s3 import read_job_config
    assert read_job_config("j1") is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/webapp/test_s3.py -k "config" -v
```

Expected: `ImportError: cannot import name 'write_job_config'`

- [ ] **Step 3: Add functions to s3.py**

Append to `webapp/s3.py` (after `upload_claude_settings`):

```python
def write_job_config(job_id: str, config: dict) -> None:
    """Write full job config (including credentials) to S3. Never written to state.json."""
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=f"jobs/{job_id}/config.json",
        Body=json.dumps(config),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def read_job_config(job_id: str) -> dict | None:
    try:
        obj = _client().get_object(
            Bucket=settings.s3_bucket, Key=f"jobs/{job_id}/config.json"
        )
        return json.loads(obj["Body"].read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/pytest tests/webapp/test_s3.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add webapp/s3.py tests/webapp/test_s3.py
git commit -m "feat: add write_job_config/read_job_config to s3.py for credential isolation"
```

---

## Task 5: Update jobs.py — SQS enqueue in create_job()

**Files:**
- Modify: `webapp/jobs.py`
- Modify: `tests/webapp/test_jobs.py`

`create_job()` now writes credentials to S3 (`config.json`) and enqueues a lightweight SQS message (`job_id` + `s3_keys` only). Threading is removed entirely.

- [ ] **Step 1: Write the failing tests**

Replace the existing `test_generate_claude_settings` test and add new `create_job` tests in `tests/webapp/test_jobs.py`:

```python
def test_create_job_enqueues_to_sqs(mocker):
    mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.s3.write_job_config")
    mock_sqs = mocker.MagicMock()
    mocker.patch("webapp.jobs.boto3.client", return_value=mock_sqs)
    mocker.patch("webapp.jobs.settings")

    from webapp.jobs import create_job
    job_id = create_job(_make_config(), ["uploads/sess/file.pdf"])

    assert mock_sqs.send_message.called
    import json
    body = json.loads(mock_sqs.send_message.call_args[1]["MessageBody"])
    assert body["job_id"] == job_id
    assert body["s3_keys"] == ["uploads/sess/file.pdf"]
    assert "notion_token" not in body
    assert "google_credentials" not in body


def test_create_job_stores_config_in_s3(mocker):
    mock_write_config = mocker.patch("webapp.jobs.s3.write_job_config")
    mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.boto3.client", return_value=mocker.MagicMock())
    mocker.patch("webapp.jobs.settings")

    from webapp.jobs import create_job
    config = _make_config()
    create_job(config, [])

    assert mock_write_config.called
    written_config = mock_write_config.call_args[0][1]
    assert written_config["notion_token"] == config["notion_token"]
    assert written_config["google_credentials"] == config["google_credentials"]


def test_create_job_does_not_spawn_thread(mocker):
    mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.s3.write_job_config")
    mocker.patch("webapp.jobs.boto3.client", return_value=mocker.MagicMock())
    mocker.patch("webapp.jobs.settings")
    thread_mock = mocker.patch("webapp.jobs.threading")

    from webapp.jobs import create_job
    create_job(_make_config(), [])

    assert not thread_mock.Thread.called


def test_generate_claude_settings_excludes_notion():
    from webapp.jobs import generate_claude_settings
    config = JobConfig(
        user_name="Alice", user_role="ic", account_manager_name="Alice",
        team_members=[], notion_token="n-tok", notion_database_id="db-id",
        google_credentials={"access_token": "g-acc", "refresh_token": "g-ref",
                             "client_id": "g-cid", "client_secret": ""},
        readai_api_key="ra-key", fireworks_api_key="fw-key",
        interview_answers={}, entropy_template_path="/tmp",
    )
    import json
    result = json.loads(generate_claude_settings(config))
    assert "notion" not in result["mcpServers"], "Notion must not be in claude_settings.json"
    assert "gmail" in result["mcpServers"]
    assert "readai" in result["mcpServers"]
    assert result["mcpServers"]["gmail"]["env"]["GMAIL_ACCESS_TOKEN"] == "g-acc"
    assert result["mcpServers"]["readai"]["env"]["READAI_API_KEY"] == "ra-key"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/webapp/test_jobs.py::test_create_job_enqueues_to_sqs tests/webapp/test_jobs.py::test_generate_claude_settings_excludes_notion -v
```

Expected: `AssertionError` on notion check, `AttributeError` on enqueue test.

- [ ] **Step 3: Update jobs.py**

Replace `webapp/jobs.py` with:

```python
# webapp/jobs.py
import json
import threading
import uuid
import boto3
from datetime import datetime, timezone

from pipeline import ingest, kimi, notion_pull, gmail_pull, readai_pull, vault_builder
from pipeline.models import JobConfig
from . import s3
from .config import settings

_STEPS = ["ingest", "wiki", "gaps", "notion", "gmail", "readai", "assembly"]

_state_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _update_state(job_id: str, **kwargs) -> None:
    """Update job state in S3. Never include credential fields (tokens, API keys)."""
    with _state_lock:
        state = s3.read_job_state(job_id) or {}
        state.update(kwargs)
        state["updated_at"] = _now()
        s3.write_job_state(job_id, state)


def update_job_state(job_id: str, **kwargs) -> None:
    """Public wrapper around _update_state for use outside this module."""
    _update_state(job_id, **kwargs)


def create_job(config_dict: dict, s3_keys: list[str]) -> str:
    job_id = str(uuid.uuid4())

    # Write full config (including credentials) to isolated S3 object
    s3.write_job_config(job_id, config_dict)

    # Write initial state — no credentials
    s3.write_job_state(job_id, {
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
    })

    # Enqueue to SQS — job_id and s3_keys only, no credentials
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    sqs.send_message(
        QueueUrl=settings.sqs_queue_url,
        MessageBody=json.dumps({"job_id": job_id, "s3_keys": s3_keys}),
    )

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
        try:
            _update_state(job_id, status="error", error=str(exc))
        except Exception:
            pass  # S3 unreachable — job stays in last known state


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
    """Generate claude_settings.json with Gmail and read.ai MCP only.
    Users connect Notion via Claude Desktop → Connections → Install Notion.
    """
    google = config.google_credentials or {}
    return json.dumps({
        "mcpServers": {
            "gmail": {
                "command": "npx",
                "args": ["-y", settings.gmail_mcp_package],
                "env": {
                    "GMAIL_ACCESS_TOKEN": google.get("access_token", ""),
                    "GMAIL_REFRESH_TOKEN": google.get("refresh_token", ""),
                    "GMAIL_CLIENT_ID": google.get("client_id", ""),
                    "GMAIL_CLIENT_SECRET": google.get("client_secret", ""),
                }
            },
            "readai": {
                "command": "npx",
                "args": ["-y", settings.readai_mcp_package],
                "env": {
                    "READAI_API_KEY": config.readai_api_key,
                }
            },
        }
    }, indent=2)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/pytest tests/webapp/test_jobs.py -v
```

Expected: all pass (some existing tests mock write_job_state; create_job tests use new SQS mocks).

- [ ] **Step 5: Run full suite to catch regressions**

```bash
.venv/bin/pytest tests/webapp/ -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add webapp/jobs.py tests/webapp/test_jobs.py
git commit -m "feat: replace threading with SQS enqueue in create_job, remove Notion from claude_settings"
```

---

## Task 6: Add worker/ module — SQS long-poll loop

**Files:**
- Create: `worker/__init__.py`
- Create: `worker/__main__.py`
- Create: `tests/worker/__init__.py`
- Create: `tests/worker/test_worker.py`

The worker polls SQS, reads config from S3, calls `run_pipeline_job()`, deletes message on success. On exception it logs but does NOT delete the message — SQS retries up to 3× then routes to DLQ.

- [ ] **Step 1: Write the failing tests**

```python
# tests/worker/__init__.py  (empty)

# tests/worker/test_worker.py
import json
import pytest


def _make_config() -> dict:
    return {
        "user_name": "Alice", "user_role": "ic", "account_manager_name": "Alice",
        "team_members": [], "notion_token": "n-tok", "notion_database_id": "db-id",
        "google_credentials": {"access_token": "g-acc", "refresh_token": "g-ref",
                                "client_id": "g-cid", "client_secret": ""},
        "readai_api_key": "ra-key", "fireworks_api_key": "fw-key",
        "interview_answers": {}, "entropy_template_path": "/tmp", "product_lines": [],
    }


def test_worker_processes_message_and_deletes_it(mocker):
    config = _make_config()
    msg = {
        "MessageId": "m1",
        "ReceiptHandle": "rh-1",
        "Body": json.dumps({"job_id": "j1", "s3_keys": []}),
    }
    mock_sqs = mocker.MagicMock()
    mock_sqs.receive_message.side_effect = [
        {"Messages": [msg]},
        {"Messages": []},   # second poll returns nothing, loop exits in test
    ]
    mocker.patch("worker.__main__.boto3.client", return_value=mock_sqs)
    mocker.patch("worker.__main__.s3.read_job_config", return_value=config)
    mock_run = mocker.patch("worker.__main__.run_pipeline_job")

    # Run one iteration only
    from worker.__main__ import _process_message
    _process_message(mock_sqs, "https://sqs/queue", msg)

    mock_run.assert_called_once_with("j1", config, [])
    mock_sqs.delete_message.assert_called_once_with(
        QueueUrl="https://sqs/queue", ReceiptHandle="rh-1"
    )


def test_worker_leaves_message_on_pipeline_failure(mocker):
    config = _make_config()
    msg = {
        "MessageId": "m2",
        "ReceiptHandle": "rh-2",
        "Body": json.dumps({"job_id": "j2", "s3_keys": []}),
    }
    mock_sqs = mocker.MagicMock()
    mocker.patch("worker.__main__.boto3.client", return_value=mock_sqs)
    mocker.patch("worker.__main__.s3.read_job_config", return_value=config)
    mocker.patch("worker.__main__.run_pipeline_job", side_effect=RuntimeError("boom"))

    from worker.__main__ import _process_message
    _process_message(mock_sqs, "https://sqs/queue", msg)

    mock_sqs.delete_message.assert_not_called()


def test_worker_deletes_message_when_config_missing(mocker):
    msg = {
        "MessageId": "m3",
        "ReceiptHandle": "rh-3",
        "Body": json.dumps({"job_id": "j3", "s3_keys": []}),
    }
    mock_sqs = mocker.MagicMock()
    mocker.patch("worker.__main__.boto3.client", return_value=mock_sqs)
    mocker.patch("worker.__main__.s3.read_job_config", return_value=None)
    mock_run = mocker.patch("worker.__main__.run_pipeline_job")

    from worker.__main__ import _process_message
    _process_message(mock_sqs, "https://sqs/queue", msg)

    mock_run.assert_not_called()
    mock_sqs.delete_message.assert_called_once()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/worker/ -v
```

Expected: `ModuleNotFoundError: No module named 'worker'`

- [ ] **Step 3: Create worker/__init__.py**

```python
# worker/__init__.py
```

- [ ] **Step 4: Create worker/__main__.py**

```python
# worker/__main__.py
import boto3
import json
import logging

from webapp import s3
from webapp.config import settings
from webapp.jobs import run_pipeline_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _process_message(sqs_client, queue_url: str, msg: dict) -> None:
    body = json.loads(msg["Body"])
    job_id = body["job_id"]
    s3_keys = body.get("s3_keys", [])
    receipt = msg["ReceiptHandle"]

    config = s3.read_job_config(job_id)
    if config is None:
        logger.error("Config not found for job %s — discarding message", job_id)
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
        return

    try:
        run_pipeline_job(job_id, config, s3_keys)
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
        logger.info("Job %s complete", job_id)
    except Exception:
        logger.exception("Job %s failed — leaving in queue for retry", job_id)
        # Do NOT delete — SQS will retry up to max receive count, then route to DLQ


def main() -> None:
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    queue_url = settings.sqs_queue_url
    logger.info("Worker started, polling %s", queue_url)

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            WaitTimeSeconds=20,
            MaxNumberOfMessages=1,
        )
        for msg in response.get("Messages", []):
            _process_message(sqs, queue_url, msg)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
.venv/bin/pytest tests/worker/ -v
```

Expected: 3 passed.

- [ ] **Step 6: Run full suite**

```bash
.venv/bin/pytest -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add worker/ tests/worker/
git commit -m "feat: add SQS worker module for ECS pipeline processing"
```

---

## Task 7: Update main.py — use shared Notion token; remove Notion OAuth from wizard

**Files:**
- Modify: `webapp/main.py`
- Modify: `webapp/templates/wizard.html`
- Modify: `tests/webapp/test_notion_api.py`
- Modify: `tests/webapp/test_wizard_submit.py`

The account-managers API endpoint and wizard submit both use `settings.notion_token` (the shared internal Notion token from Secrets Manager). The Notion OAuth connection step is removed from the wizard.

- [ ] **Step 1: Write the failing tests**

In `tests/webapp/test_notion_api.py`, replace existing tests with:

```python
def test_notion_account_managers_uses_shared_token(client, mocker):
    mocker.patch("webapp.main.settings").notion_token = "shared-notion-tok"
    mocker.patch("webapp.main.settings").notion_database_id = "db-123"
    mock_resp = mocker.MagicMock()
    mock_resp.json.return_value = {
        "results": [{"properties": {"Account Manager": {"people": [{"name": "Alice"}]}}}],
        "has_more": False,
        "next_cursor": None,
    }
    mock_resp.raise_for_status = lambda: None
    mocker.patch("webapp.main.requests.post", return_value=mock_resp)

    resp = client.get("/api/notion/account-managers")
    assert resp.status_code == 200
    data = resp.json()
    assert "Alice" in data["managers"]


def test_notion_account_managers_no_session_required(client, mocker):
    # Endpoint no longer requires session_id — uses shared token
    mocker.patch("webapp.main.settings").notion_token = "shared-tok"
    mocker.patch("webapp.main.settings").notion_database_id = "db-123"
    mock_resp = mocker.MagicMock()
    mock_resp.json.return_value = {"results": [], "has_more": False, "next_cursor": None}
    mock_resp.raise_for_status = lambda: None
    mocker.patch("webapp.main.requests.post", return_value=mock_resp)

    # Call without session_id — should work fine
    resp = client.get("/api/notion/account-managers")
    assert resp.status_code == 200
```

Add to `tests/webapp/test_wizard_submit.py`:

```python
def test_wizard_submit_uses_shared_notion_token(client, mocker):
    from unittest.mock import patch
    mocker.patch("webapp.main.settings").notion_token = "shared-secret-tok"
    mocker.patch("webapp.main.settings").notion_database_id = "db-id"
    mocker.patch("webapp.main.settings").fireworks_api_key = "fw-key"
    mocker.patch("webapp.main.settings").entropy_template_path = "/tmp"
    mocker.patch("webapp.main.settings").sqs_queue_url = "https://sqs/test"
    mocker.patch("webapp.main.settings").aws_region = "us-east-1"

    google_tok = {"access_token": "g-acc", "refresh_token": "g-ref"}
    from webapp import session
    session_id = "33333333-3333-3333-3333-333333333333"
    session.set_session_value(session_id, "google_tokens", google_tok)

    mock_create = mocker.patch("webapp.main.jobs.create_job", return_value="job-abc")

    resp = client.post("/api/wizard/submit", json={
        "session_id": session_id,
        "s3_keys": [f"uploads/{session_id}/file.pdf"],
        "user_name": "Bob", "user_role": "ic", "account_manager_name": "Bob",
        "team_members": [], "interview_answers": {}, "readai_api_key": "rk",
    })
    assert resp.status_code == 200
    config_passed = mock_create.call_args[0][0]
    assert config_passed["notion_token"] == "shared-secret-tok"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/webapp/test_notion_api.py tests/webapp/test_wizard_submit.py::test_wizard_submit_uses_shared_notion_token -v
```

Expected: failures — endpoint still requires session_id / uses per-user token.

- [ ] **Step 3: Update /api/notion/account-managers in main.py**

Find the `notion_account_managers` function in `webapp/main.py`. Change the signature and token source:

```python
@app.get("/api/notion/account-managers")
def notion_account_managers():
    access_token = settings.notion_token
    if not access_token:
        raise HTTPException(status_code=503, detail="Notion not configured")
    managers: set[str] = set()
    cursor = None
    for _ in range(50):
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        try:
            resp = requests.post(
                f"https://api.notion.com/v1/databases/{settings.notion_database_id}/query",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 502
            if status == 401:
                raise HTTPException(status_code=401, detail="Notion token invalid")
            raise HTTPException(status_code=502, detail="Notion API error")
        except requests.RequestException:
            raise HTTPException(status_code=504, detail="Notion API timeout")
        data = resp.json()
        for row in data.get("results", []):
            props = row.get("properties", {})
            am_prop = props.get("Account Manager", {})
            for person in am_prop.get("people", []):
                if person.get("name"):
                    managers.add(person["name"])
        if not data.get("has_more") or not data.get("next_cursor"):
            break
        cursor = data.get("next_cursor")
    return {"managers": sorted(managers)}
```

- [ ] **Step 4: Update wizard_submit in main.py to use settings.notion_token**

Find the `wizard_submit` handler. Change:

```python
notion_tokens = get_token(req.session_id, "notion")
config_dict = {
    ...
    "notion_token": notion_tokens["access_token"] if notion_tokens else "",
    ...
}
```

To:

```python
config_dict = {
    ...
    "notion_token": settings.notion_token,
    ...
}
```

Remove the `notion_tokens = get_token(...)` line entirely.

- [ ] **Step 5: Remove Notion OAuth step from wizard.html**

In `webapp/templates/wizard.html`, find and remove:
- The Notion connect button / step section (the `<div>` or `<section>` containing "Connect Notion" or similar)
- The `loadTeamMembers` call that fetches from `/api/notion/account-managers?session_id=...` — update it to call `/api/notion/account-managers` (no `session_id` param)
- Any `openOAuth('notion')` call

The account managers dropdown should still load on that wizard step — just call `/api/notion/account-managers` without a `session_id` query parameter.

- [ ] **Step 6: Run all tests**

```bash
.venv/bin/pytest tests/webapp/ tests/worker/ -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add webapp/main.py webapp/templates/wizard.html tests/webapp/test_notion_api.py tests/webapp/test_wizard_submit.py
git commit -m "feat: use shared Notion token for account-managers API and pipeline; remove per-user Notion OAuth"
```

---

## Task 8: Update status.html — 4-step setup guide

**Files:**
- Modify: `webapp/templates/status.html`
- Modify: `tests/webapp/test_status.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/webapp/test_status.py`:

```python
def test_status_page_includes_notion_desktop_step(client, mocker):
    resp = client.get("/job/some-job-id")
    assert resp.status_code == 200
    assert b"Install Notion" in resp.content or b"Connections" in resp.content
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
.venv/bin/pytest tests/webapp/test_status.py::test_status_page_includes_notion_desktop_step -v
```

Expected: FAIL — current guide has 3 steps, no Notion desktop step.

- [ ] **Step 3: Update the setup guide in status.html**

Find the `<ol>` setup guide section and replace it:

```html
<ol class="space-y-3 text-sm text-slate-600 list-decimal list-inside">
  <li>Install Obsidian (obsidian.md). Unzip entropy-vault.zip and open the folder as a vault.</li>
  <li>Install Claude Desktop (claude.ai/download). Place claude_settings.json in ~/Library/Application Support/Claude/ (Mac) or %APPDATA%\Claude\ (Windows).</li>
  <li>Open Claude Desktop → Settings → Connections → Install Notion.</li>
  <li>Open Claude Desktop and ask: "What's the state of my portfolio?" — you're live.</li>
</ol>
```

- [ ] **Step 4: Run all tests**

```bash
.venv/bin/pytest tests/webapp/ tests/worker/ -q
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add webapp/templates/status.html tests/webapp/test_status.py
git commit -m "feat: update setup guide to 4 steps with Notion via Claude Desktop Connections"
```

---

## Self-Review

### 1. Spec coverage

| Spec requirement | Task covering it |
|---|---|
| entropy-template bundled in Docker image | Task 1 + Task 2 |
| Dockerfile for web + worker (same image) | Task 2 |
| `sqs_queue_url` + `notion_token` in config | Task 3 |
| S3 config storage (`write_job_config`) | Task 4 |
| `create_job()` enqueues to SQS | Task 5 |
| `generate_claude_settings()` omits Notion | Task 5 |
| `worker/__main__.py` SQS poll loop | Task 6 |
| Account-managers uses shared Notion token | Task 7 |
| Wizard submit uses shared Notion token | Task 7 |
| Notion OAuth step removed from wizard | Task 7 |
| Status page 4-step setup guide | Task 8 |

### 2. Placeholder scan

None found.

### 3. Type consistency

- `_process_message(sqs_client, queue_url, msg)` — consistent across Task 6 tests and implementation.
- `s3.write_job_config(job_id, config_dict)` / `s3.read_job_config(job_id)` — consistent across Tasks 4, 5, and 6.
- `create_job(config_dict, s3_keys) -> str` — unchanged signature, consistent with Task 5 tests.
