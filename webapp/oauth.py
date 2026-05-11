import re
import urllib.parse
import requests
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from .config import settings
from .session import set_session_value, get_token

router = APIRouter()

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_SCOPES = "openid email https://www.googleapis.com/auth/gmail.readonly"

_NOTION_AUTH_URL = "https://api.notion.com/v1/oauth/authorize"
_NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"

_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


def _validate_state(state: str) -> None:
    """Reject non-UUID state parameters to prevent CSRF/DoS."""
    if not _UUID_RE.match(state):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


_POPUP_HTML = """<!DOCTYPE html>
<html><head><title>Connecting...</title></head><body>
<script>
(function(){{
  var msg = {{provider: '{provider}', success: true, verified: {verified}}};
  if (window.opener) {{ window.opener.postMessage(msg, window.location.origin); window.close(); }}
  else {{ document.body.textContent = '{provider} connected. You can close this window.'; }}
}})();
</script>
</body></html>"""

_POPUP_FAIL_HTML = """<!DOCTYPE html>
<html><head><title>Connection failed</title></head><body>
<script>
(function(){{
  var msg = {{provider: '{provider}', success: false, verified: false}};
  if (window.opener) {{ window.opener.postMessage(msg, window.location.origin); window.close(); }}
  else {{ document.body.textContent = '{provider} connection failed. You can close this window.'; }}
}})();
</script>
</body></html>"""


@router.get("/oauth/google")
def google_start(session_id: str):
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.base_url}/oauth/google/callback",
        "response_type": "code",
        "scope": _GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": session_id,
    }
    return RedirectResponse(_GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params))


@router.get("/oauth/google/callback")
def google_callback(code: str, state: str):
    _validate_state(state)
    try:
        resp = requests.post(_GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": f"{settings.base_url}/oauth/google/callback",
            "grant_type": "authorization_code",
        }, timeout=15)
        resp.raise_for_status()
        tokens = resp.json()
    except Exception:
        return HTMLResponse(_POPUP_FAIL_HTML.format(provider="google"))
    set_session_value(state, "google_tokens", tokens)
    verified = _verify_google(tokens.get("access_token", ""))
    return HTMLResponse(_POPUP_HTML.format(
        provider="google",
        verified="true" if verified else "false",
    ))


@router.get("/oauth/notion")
def notion_start(session_id: str):
    params = {
        "client_id": settings.notion_client_id,
        "redirect_uri": f"{settings.base_url}/oauth/notion/callback",
        "response_type": "code",
        "owner": "user",
        "state": session_id,
    }
    return RedirectResponse(_NOTION_AUTH_URL + "?" + urllib.parse.urlencode(params))


@router.get("/oauth/notion/callback")
def notion_callback(code: str, state: str):
    _validate_state(state)
    try:
        resp = requests.post(
            _NOTION_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.base_url}/oauth/notion/callback",
            },
            auth=(settings.notion_client_id, settings.notion_client_secret),
            timeout=15,
        )
        resp.raise_for_status()
        tokens = resp.json()
    except Exception:
        return HTMLResponse(_POPUP_FAIL_HTML.format(provider="notion"))
    set_session_value(state, "notion_tokens", tokens)
    verified = _verify_notion(tokens.get("access_token", ""))
    return HTMLResponse(_POPUP_HTML.format(
        provider="notion",
        verified="true" if verified else "false",
    ))


@router.get("/api/session/{session_id}/tokens")
def session_tokens(session_id: str):
    return {
        "google": get_token(session_id, "google") is not None,
        "notion": get_token(session_id, "notion") is not None,
    }


def _verify_google(access_token: str) -> bool:
    """Test query: list Gmail labels — fast, confirms auth works."""
    try:
        resp = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/labels",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _verify_notion(access_token: str) -> bool:
    """Test query: query shared Notion DB for 1 row — confirms DB access works."""
    try:
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{settings.notion_database_id}/query",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={"page_size": 1},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False
