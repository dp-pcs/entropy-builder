import re
import urllib.parse
import uuid
import requests
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from .config import settings
from .session import set_session_value, get_token
from .auth import create_auth_token
from . import db

router = APIRouter()

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_SCOPES = "openid email https://www.googleapis.com/auth/gmail.readonly"

_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

_AUTH_COOKIE = "entropy_auth"
_AUTH_MAX_AGE = 30 * 86400  # 30 days


def _validate_state(state: str) -> None:
    if not _UUID_RE.match(state):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


def _set_auth_cookie(response, token: str):
    response.set_cookie(
        _AUTH_COOKIE, token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_AUTH_MAX_AGE,
    )


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
    _validate_state(session_id)
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
    user_info = _upsert_google_user(state, tokens.get("access_token", ""))
    verified = _verify_google(tokens.get("access_token", ""))

    html = _POPUP_HTML.format(provider="google", verified="true" if verified else "false")
    response = HTMLResponse(html)
    if user_info:
        token = create_auth_token(
            user_info["google_sub"], user_info.get("email", ""), user_info.get("name", "")
        )
        _set_auth_cookie(response, token)
    return response


@router.get("/oauth/google/return")
def google_return():
    """Full-page OAuth flow for returning users who want to retrieve their vault."""
    nonce = str(uuid.uuid4())
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.base_url}/oauth/google/return/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "state": nonce,
    }
    return RedirectResponse(_GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params))


@router.get("/oauth/google/return/callback")
def google_return_callback(code: str, state: str = ""):
    """Exchanges code, looks up DynamoDB, sets auth cookie, redirects to last job or wizard."""
    try:
        resp = requests.post(_GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": f"{settings.base_url}/oauth/google/return/callback",
            "grant_type": "authorization_code",
        }, timeout=15)
        resp.raise_for_status()
        tokens = resp.json()
        ui = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            timeout=10,
        ).json()
        google_sub = ui.get("sub", "")
    except Exception:
        return RedirectResponse("/?return_error=1")
    if not google_sub:
        return RedirectResponse("/?return_error=1")
    try:
        db.upsert_user(google_sub, ui.get("email", ""), ui.get("name", ""))
        user = db.get_user(google_sub)
        latest_job_id = user.get("latest_job_id") if user else None
    except Exception:
        latest_job_id = None

    dest = f"/job/{latest_job_id}" if latest_job_id else "/wizard"
    response = RedirectResponse(dest)
    auth_token = create_auth_token(google_sub, ui.get("email", ""), ui.get("name", ""))
    _set_auth_cookie(response, auth_token)
    return response


@router.get("/api/session/{session_id}/tokens")
def session_tokens(session_id: str):
    return {
        "google": get_token(session_id, "google") is not None,
        "notion": get_token(session_id, "notion") is not None,
    }


def _upsert_google_user(session_id: str, access_token: str) -> dict | None:
    """Fetch Google identity, persist to DynamoDB, return user info dict. Silently swallows errors."""
    try:
        ui = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()
        google_sub = ui.get("sub", "")
        if google_sub:
            set_session_value(session_id, "google_sub", google_sub)
            db.upsert_user(google_sub, ui.get("email", ""), ui.get("name", ""))
            return {"google_sub": google_sub, "email": ui.get("email", ""), "name": ui.get("name", "")}
    except Exception:
        pass
    return None


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
