import pytest


def test_status_api_returns_job_state(client, mocker):
    mocker.patch("webapp.main.s3.read_job_state", return_value={
        "job_id": "j1", "status": "processing", "step": "wiki",
        "step_index": 1, "total_steps": 7, "gaps": [], "gap_s3_keys": [],
        "vault_key": None, "claude_settings_key": None, "error": None,
        "created_at": "2026-05-11T00:00:00Z", "updated_at": "2026-05-11T00:01:00Z",
    })
    resp = client.get("/api/job/j1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processing"
    assert data["step"] == "wiki"
    assert "vault_download_url" not in data


def test_status_api_includes_download_url_when_complete(client, mocker):
    mocker.patch("webapp.main.s3.read_job_state", return_value={
        "job_id": "j1", "status": "complete", "step": "complete",
        "step_index": 7, "total_steps": 7, "gaps": [], "gap_s3_keys": [],
        "vault_key": "jobs/j1/entropy-vault.zip",
        "claude_settings_key": "jobs/j1/claude_settings.json",
        "error": None, "created_at": "", "updated_at": "",
    })
    mocker.patch("webapp.main.s3.presign_download",
                 side_effect=lambda key, **kw: "https://s3.example.com/" + key)

    resp = client.get("/api/job/j1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "complete"
    assert "vault_download_url" in data
    assert "claude_settings_download_url" in data
    assert "entropy-vault.zip" in data["vault_download_url"]


def test_status_api_404_for_missing_job(client, mocker):
    mocker.patch("webapp.main.s3.read_job_state", return_value=None)
    resp = client.get("/api/job/no-such-job/status")
    assert resp.status_code == 404


def test_status_page_route_exists(client, mocker):
    resp = client.get("/job/some-job-id")
    assert resp.status_code in (200, 500)


def test_gap_presign_stores_key(client, mocker):
    mocker.patch("webapp.main.s3.read_job_state", return_value={
        "job_id": "j1", "status": "processing", "gap_s3_keys": [],
    })
    mocker.patch("webapp.main.s3.write_job_state")
    mocker.patch("webapp.main.s3.presign_upload", return_value="https://s3.example.com/gap-upload")

    resp = client.post("/api/job/j1/gaps/presign", json={
        "session_id": "sess-1",
        "filename": "additional-notes.pdf",
        "content_type": "application/pdf",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["upload_url"] == "https://s3.example.com/gap-upload"
    assert "s3_key" in data
