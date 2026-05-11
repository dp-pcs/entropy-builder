import pytest

_VALID_PAYLOAD = {
    "session_id": "11111111-1111-1111-1111-111111111111",
    "user_role": "ic",
    "user_name": "Alice Johnson",
    "account_manager_name": "Alice Johnson",
    "team_members": [],
    "readai_api_key": "ra-key",
    "s3_keys": ["uploads/11111111-1111-1111-1111-111111111111/notes.pdf"],
    "interview_answers": {"books": "Never Split the Difference", "frameworks": "MEDDICC"},
}


def test_wizard_submit_returns_job_id(client, mocker):
    from webapp.session import set_session_value
    set_session_value("11111111-1111-1111-1111-111111111111", "google_tokens", {
        "access_token": "g-acc", "refresh_token": "g-ref",
    })
    set_session_value("11111111-1111-1111-1111-111111111111", "notion_tokens", {"access_token": "n-tok"})

    mocker.patch("webapp.jobs.s3.write_job_state")
    mock_thread = mocker.patch("webapp.jobs.threading.Thread")
    mock_thread.return_value.start = lambda: None
    mocker.patch("webapp.main.settings.notion_database_id", "db-id")
    mocker.patch("webapp.main.settings.fireworks_api_key", "fw-key")
    mocker.patch("webapp.main.settings.entropy_template_path", "/tmp")

    resp = client.post("/api/wizard/submit", json=_VALID_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID format


def test_wizard_submit_missing_name_returns_422(client):
    payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "user_name"}
    resp = client.post("/api/wizard/submit", json=payload)
    assert resp.status_code == 422


def test_wizard_submit_requires_google_connection(client, mocker):
    mocker.patch("webapp.main.settings.fireworks_api_key", "fw-key")
    mocker.patch("webapp.main.settings.entropy_template_path", "/tmp")
    # No Google token in session — use a fresh UUID that has no tokens
    payload = dict(_VALID_PAYLOAD, session_id="22222222-2222-2222-2222-222222222222")
    resp = client.post("/api/wizard/submit", json=payload)
    assert resp.status_code == 400
    assert "Google" in resp.json()["detail"]
