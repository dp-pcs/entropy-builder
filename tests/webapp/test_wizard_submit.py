import pytest
from unittest.mock import MagicMock

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
    from webapp.jobs import run_pipeline_job
    set_session_value("11111111-1111-1111-1111-111111111111", "google_tokens", {
        "access_token": "g-acc", "refresh_token": "g-ref",
    })
    set_session_value("11111111-1111-1111-1111-111111111111", "notion_tokens", {"access_token": "n-tok"})

    mock_write = mocker.patch("webapp.jobs.s3.write_job_state")
    mock_thread = mocker.patch("webapp.jobs.threading.Thread")
    mock_thread.return_value.start = MagicMock()
    mocker.patch("webapp.main.settings.notion_database_id", "db-id")
    mocker.patch("webapp.main.settings.fireworks_api_key", "fw-key")
    mocker.patch("webapp.main.settings.entropy_template_path", "/tmp")

    resp = client.post("/api/wizard/submit", json=_VALID_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36

    # Assert thread was created correctly
    mock_thread.assert_called_once()
    call_kwargs = mock_thread.call_args.kwargs if mock_thread.call_args.kwargs else {}
    call_args = mock_thread.call_args.args if mock_thread.call_args.args else ()
    assert mock_thread.return_value.start.called

    # Assert initial S3 state shape
    assert mock_write.call_count >= 1
    first_write_state = mock_write.call_args_list[0][0][1]
    assert first_write_state["status"] == "pending"
    assert first_write_state["step"] == "ingest"
    assert first_write_state["step_index"] == 0
    assert first_write_state["total_steps"] == 7
    assert first_write_state["gaps"] == []
    assert first_write_state["vault_key"] is None


def test_wizard_submit_missing_name_returns_422(client):
    payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "user_name"}
    resp = client.post("/api/wizard/submit", json=payload)
    assert resp.status_code == 422


def test_wizard_submit_rejects_foreign_s3_key(client, mocker):
    mocker.patch("webapp.main.s3.write_job_state")
    resp = client.post("/api/wizard/submit", json={
        "session_id": "11111111-1111-1111-1111-111111111111",
        "s3_keys": ["uploads/22222222-2222-2222-2222-222222222222/evil.pdf"],
        "user_name": "Test", "user_role": "ic", "account_manager_name": "Test",
        "team_members": [], "interview_answers": {},
        "notion_database_id": "abc", "readai_api_key": "rk_test",
    })
    assert resp.status_code == 400


def test_wizard_submit_requires_google_connection(client, mocker):
    mocker.patch("webapp.main.settings.fireworks_api_key", "fw-key")
    mocker.patch("webapp.main.settings.entropy_template_path", "/tmp")
    # No Google token in session — use a fresh UUID that has no tokens
    # s3_keys must match the new session_id prefix to pass the prefix check
    new_session_id = "22222222-2222-2222-2222-222222222222"
    payload = dict(
        _VALID_PAYLOAD,
        session_id=new_session_id,
        s3_keys=[f"uploads/{new_session_id}/notes.pdf"],
    )
    resp = client.post("/api/wizard/submit", json=payload)
    assert resp.status_code == 400
    assert "Google" in resp.json()["detail"]
