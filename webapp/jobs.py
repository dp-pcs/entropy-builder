# webapp/jobs.py
import threading
import uuid
from datetime import datetime, timezone

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
    """Implemented in Task 7."""
    pass
