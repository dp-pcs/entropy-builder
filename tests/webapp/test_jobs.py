# tests/webapp/test_jobs.py
import json
import pytest
from pipeline.models import JobConfig, CustomerRecord, VaultFile, GapItem


def test_create_job_persists_s3_keys(mocker):
    """create_job must write inputs.json so /rebuild can recover s3_keys later."""
    from webapp import jobs
    write_config = mocker.patch("webapp.jobs.s3.write_job_config")
    write_inputs = mocker.patch("webapp.jobs.s3.write_job_inputs")
    mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.boto3.client")

    s3_keys = ["uploads/sess-1/a.pdf", "uploads/sess-1/b.zip"]
    job_id = jobs.create_job(_make_config(), s3_keys, owner_sub="user-123")

    write_config.assert_called_once()
    write_inputs.assert_called_once_with(job_id, s3_keys)


def test_rebuild_job_endpoint(mocker, client):
    """POST /api/job/{id}/rebuild mints a new job_id reusing the original
    config + s3_keys, without re-uploading or re-pasting interview answers."""
    original_job = "00000000-0000-0000-0000-000000000001"
    config_dict = _make_config()
    s3_keys = ["uploads/sess-orig/notes.zip"]

    mocker.patch("webapp.main.s3.read_job_state",
                 return_value={"owner_sub": "", "status": "complete"})
    mocker.patch("webapp.main.s3.read_job_config", return_value=config_dict)
    mocker.patch("webapp.main.s3.read_job_inputs", return_value=s3_keys)
    create_job = mocker.patch("webapp.jobs.create_job", return_value="new-job-uuid")

    resp = client.post(f"/api/job/{original_job}/rebuild")
    assert resp.status_code == 200
    assert resp.json() == {"job_id": "new-job-uuid"}
    create_job.assert_called_once_with(config_dict, s3_keys, owner_sub="")


def test_rebuild_job_404_when_missing(mocker, client):
    mocker.patch("webapp.main.s3.read_job_state", return_value=None)
    resp = client.post("/api/job/00000000-0000-0000-0000-000000000099/rebuild")
    assert resp.status_code == 404


def test_rebuild_job_409_when_inputs_not_persisted(mocker, client):
    """Jobs created before the rebuild feature didn't persist s3_keys —
    return a clear 409 instead of crashing or silently rebuilding empty."""
    mocker.patch("webapp.main.s3.read_job_state",
                 return_value={"owner_sub": "", "status": "complete"})
    mocker.patch("webapp.main.s3.read_job_config", return_value=_make_config())
    mocker.patch("webapp.main.s3.read_job_inputs", return_value=None)

    resp = client.post("/api/job/00000000-0000-0000-0000-000000000002/rebuild")
    assert resp.status_code == 409
    assert "rebuild" in resp.json()["detail"].lower()


def _make_config() -> dict:
    return {
        "user_name": "Alice Johnson",
        "user_role": "ic",
        "account_manager_name": "Alice Johnson",
        "team_members": [],
        "notion_token": "n-tok",
        "notion_database_id": "db-id",
        "google_credentials": {"access_token": "g-acc", "refresh_token": "g-ref",
                                "client_id": "g-cid", "client_secret": "g-csec"},
        "readai_access_token": "ra-key",
        "fireworks_api_key": "fw-key",
        "interview_answers": {"books": "Atomic Habits"},
        "entropy_template_path": "/tmp",
        "product_lines": [],
    }


def _make_customer() -> CustomerRecord:
    return CustomerRecord(
        name="Acme", product="Tivian", sub_product="DXI", arr=50000.0,
        renewal_date="2026-12-01", status_tags=["HVO"], success_level="Platinum",
        contract_term=12, esw_paper=False, primary_contact="Jane",
        primary_email="jane@acme.com", additional_contacts="", champion="Jane",
        detractor="", decision_maker="Jane", influencer="",
        product_sentiment="Positive", support_sentiment="Positive",
        renewals_sentiment="Positive", product_feedback="", account_notes="",
    )


def test_run_pipeline_job_happy_path(mocker):
    from webapp.jobs import run_pipeline_job

    mock_write = mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.s3.read_job_state", return_value={
        "job_id": "j1", "status": "pending", "step": "ingest", "step_index": 0,
        "total_steps": 7, "gaps": [], "gap_s3_keys": [], "vault_key": None,
        "claude_settings_key": None, "error": None, "created_at": "", "updated_at": "",
    })
    mocker.patch("webapp.jobs.s3.upload_vault", return_value="jobs/j1/entropy-vault.zip")
    mocker.patch("webapp.jobs.s3.upload_claude_settings", return_value="jobs/j1/claude_settings.json")
    mocker.patch("webapp.jobs._download_s3_files", return_value=[])
    mocker.patch("webapp.jobs.ingest.ingest", return_value=[])
    mocker.patch("webapp.jobs.kimi.generate_wiki", return_value=[VaultFile("User-Profile.md", "# Profile")])
    mocker.patch("webapp.jobs.kimi.analyze_gaps", return_value=[
        GapItem(category="books", description="No books", prompt="List some books", upload_accepted=True)
    ])
    mocker.patch("webapp.jobs.notion_pull.pull_customers", return_value=[_make_customer()])
    mocker.patch("webapp.jobs.notion_pull.build_intelligence_summary", return_value=VaultFile("Tivian/Acme/_intelligence_summary.md", "# Acme"))
    mocker.patch("webapp.jobs.notion_pull.build_customer_domains", return_value=VaultFile("Entropy/_data/customer_domains.json", '{"version":"1.0","generated":"today","domains":{}}'))
    mocker.patch("webapp.jobs.notion_pull.build_hub_nodes", return_value=[])
    mocker.patch("webapp.jobs.gmail_pull.pull_emails", return_value=[])
    mocker.patch("webapp.jobs.readai_pull.pull_transcripts", return_value=[])
    mocker.patch("webapp.jobs.vault_builder.build_vault", return_value=b"ZIPDATA")

    run_pipeline_job("j1", _make_config(), [])

    final_state = mock_write.call_args_list[-1][0][1]
    assert final_state["status"] == "complete"
    assert final_state["vault_key"] == "jobs/j1/entropy-vault.zip"
    assert final_state["claude_settings_key"] == "jobs/j1/claude_settings.json"
    assert len(final_state["gaps"]) == 1
    # Verify no credentials in final state
    assert "notion_token" not in final_state
    assert "google_credentials" not in final_state


def test_run_pipeline_job_error_path(mocker):
    from webapp.jobs import run_pipeline_job

    mock_write = mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.s3.read_job_state", return_value={
        "job_id": "j2", "status": "pending", "step": "ingest", "step_index": 0,
        "total_steps": 7, "gaps": [], "gap_s3_keys": [], "vault_key": None,
        "claude_settings_key": None, "error": None, "created_at": "", "updated_at": "",
    })
    mocker.patch("webapp.jobs._download_s3_files", return_value=[])
    mocker.patch("webapp.jobs.ingest.ingest", side_effect=RuntimeError("ingest failed"))

    import pytest
    with pytest.raises(RuntimeError, match="ingest failed"):
        run_pipeline_job("j2", _make_config(), [])

    error_state = mock_write.call_args_list[-1][0][1]
    assert error_state["status"] == "error"
    assert "ingest failed" in error_state["error"]
    # Verify no credentials in error state
    assert "notion_token" not in error_state
    assert "google_credentials" not in error_state


def test_run_pipeline_job_notion_failure(mocker):
    from webapp.jobs import run_pipeline_job

    mock_write = mocker.patch("webapp.jobs.s3.write_job_state")
    mocker.patch("webapp.jobs.s3.read_job_state", return_value={
        "job_id": "j3", "status": "pending", "step": "ingest", "step_index": 0,
        "total_steps": 7, "gaps": [], "gap_s3_keys": [], "vault_key": None,
        "claude_settings_key": None, "error": None, "created_at": "", "updated_at": "",
    })
    mocker.patch("webapp.jobs._download_s3_files", return_value=[])
    mocker.patch("webapp.jobs.ingest.ingest", return_value=[])
    mocker.patch("webapp.jobs.kimi.generate_wiki", return_value=[])
    mocker.patch("webapp.jobs.kimi.analyze_gaps", return_value=[])
    mocker.patch("webapp.jobs.notion_pull.pull_customers",
                 side_effect=RuntimeError("Notion API 429"))

    config = {
        "user_name": "Alice", "user_role": "ic", "account_manager_name": "Alice",
        "team_members": [], "notion_token": "n-tok", "notion_database_id": "db-id",
        "google_credentials": {"access_token": "g-acc", "refresh_token": "g-ref",
                                "client_id": "g-cid", "client_secret": "g-csec"},
        "readai_access_token": "ra-key", "fireworks_api_key": "fw-key",
        "interview_answers": {}, "entropy_template_path": "/tmp", "product_lines": [],
    }
    import pytest
    with pytest.raises(RuntimeError, match="Notion API 429"):
        run_pipeline_job("j3", config, [])

    error_state = mock_write.call_args_list[-1][0][1]
    assert error_state["status"] == "error"
    assert "Notion API 429" in error_state["error"]


def test_generate_claude_settings():
    from webapp.jobs import generate_claude_settings
    config = JobConfig(
        user_name="Alice", user_role="ic", account_manager_name="Alice",
        team_members=[], notion_token="n-tok", notion_database_id="db-id",
        google_credentials={"access_token": "g-acc", "refresh_token": "g-ref",
                             "client_id": "g-cid", "client_secret": "g-csec"},
        readai_access_token="ra-key", fireworks_api_key="fw-key",
        interview_answers={}, entropy_template_path="/tmp",
    )
    result = json.loads(generate_claude_settings(config))
    assert "mcpServers" in result
    assert "notion" not in result["mcpServers"]
    assert "gmail" in result["mcpServers"]
    assert "readai" in result["mcpServers"]
    assert result["mcpServers"]["gmail"]["env"]["GMAIL_ACCESS_TOKEN"] == "g-acc"
    assert result["mcpServers"]["readai"]["env"]["READAI_API_KEY"] == "ra-key"
