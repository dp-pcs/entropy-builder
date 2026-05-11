import pytest
from unittest.mock import MagicMock


def test_google_oauth_start_redirects(client, mocker):
    mocker.patch("webapp.oauth.settings.google_client_id", "test-client-id")
    mocker.patch("webapp.oauth.settings.base_url", "http://localhost:8000")
    resp = client.get("/oauth/google?session_id=sess-1", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "accounts.google.com" in resp.headers["location"]
    assert "test-client-id" in resp.headers["location"]
    assert "sess-1" in resp.headers["location"]


def test_google_oauth_callback_stores_tokens_and_closes(client, mocker):
    mock_post = mocker.patch("webapp.oauth.requests.post")
    mock_post.return_value.json.return_value = {
        "access_token": "acc-tok",
        "refresh_token": "ref-tok",
        "token_type": "Bearer",
    }
    mock_post.return_value.raise_for_status = lambda: None
    mocker.patch("webapp.oauth._verify_google", return_value=True)
    mocker.patch("webapp.oauth.settings.google_client_id", "cid")
    mocker.patch("webapp.oauth.settings.google_client_secret", "csec")
    mocker.patch("webapp.oauth.settings.base_url", "http://localhost:8000")

    resp = client.get("/oauth/google/callback?code=authcode&state=sess-1")
    assert resp.status_code == 200
    assert "window.opener" in resp.text
    assert "google" in resp.text

    from webapp.session import get_token
    tokens = get_token("sess-1", "google")
    assert tokens["access_token"] == "acc-tok"


def test_notion_oauth_start_redirects(client, mocker):
    mocker.patch("webapp.oauth.settings.notion_client_id", "notion-cid")
    mocker.patch("webapp.oauth.settings.base_url", "http://localhost:8000")
    resp = client.get("/oauth/notion?session_id=sess-2", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "notion.com" in resp.headers["location"]


def test_notion_oauth_callback_stores_token(client, mocker):
    mock_post = mocker.patch("webapp.oauth.requests.post")
    mock_post.return_value.json.return_value = {
        "access_token": "notion-tok",
        "workspace_id": "ws-123",
    }
    mock_post.return_value.raise_for_status = lambda: None
    mocker.patch("webapp.oauth._verify_notion", return_value=True)
    mocker.patch("webapp.oauth.settings.notion_client_id", "ncid")
    mocker.patch("webapp.oauth.settings.notion_client_secret", "nsec")
    mocker.patch("webapp.oauth.settings.base_url", "http://localhost:8000")

    resp = client.get("/oauth/notion/callback?code=ncode&state=sess-2")
    assert resp.status_code == 200
    assert "notion" in resp.text

    from webapp.session import get_token
    tokens = get_token("sess-2", "notion")
    assert tokens["access_token"] == "notion-tok"


def test_session_tokens_endpoint(client):
    from webapp.session import set_session_value
    set_session_value("sess-3", "google_tokens", {"access_token": "g-tok"})
    set_session_value("sess-3", "notion_tokens", {"access_token": "n-tok"})

    resp = client.get("/api/session/sess-3/tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["google"] is True
    assert data["notion"] is True


def test_session_tokens_endpoint_empty(client):
    resp = client.get("/api/session/no-such-session/tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["google"] is False
    assert data["notion"] is False
