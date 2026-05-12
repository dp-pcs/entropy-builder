import base64
import hashlib
import os as _os
import re
import urllib.parse
import uuid
import requests
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from .config import settings
from .session import set_session_value, get_session_value, get_token
from .auth import create_auth_token
from . import db

router = APIRouter()

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_SCOPES_PM    = "openid email https://www.googleapis.com/auth/gmail.readonly"
_GOOGLE_SCOPES_OTHER = "openid email https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/drive.readonly"

_READAI_AUTH_URL = "https://authn.read.ai/oauth2/auth"
_READAI_TOKEN_URL = "https://authn.read.ai/oauth2/token"
_READAI_SCOPES = "openid email offline_access meeting:read"


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(_os.urandom(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge

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
def google_start(session_id: str, persona: str = "pm"):
    _validate_state(session_id)
    scopes = _GOOGLE_SCOPES_OTHER if persona != "pm" else _GOOGLE_SCOPES_PM
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.base_url}/oauth/google/callback",
        "response_type": "code",
        "scope": scopes,
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


@router.get("/oauth/readai")
def readai_start(session_id: str):
    _validate_state(session_id)
    verifier, challenge = _pkce_pair()
    set_session_value(session_id, "readai_code_verifier", verifier)
    params = {
        "client_id": settings.readai_client_id,
        "redirect_uri": f"{settings.base_url}/oauth/readai/callback",
        "response_type": "code",
        "scope": _READAI_SCOPES,
        "state": session_id,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return RedirectResponse(_READAI_AUTH_URL + "?" + urllib.parse.urlencode(params))


@router.get("/oauth/readai/callback")
def readai_callback(code: str, state: str):
    _validate_state(state)
    verifier = get_session_value(state, "readai_code_verifier")
    if not verifier:
        return HTMLResponse(_POPUP_FAIL_HTML.format(provider="readai"))
    try:
        resp = requests.post(_READAI_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{settings.base_url}/oauth/readai/callback",
            "client_id": settings.readai_client_id,
            "code_verifier": verifier,
        }, timeout=15)
        resp.raise_for_status()
        tokens = resp.json()
    except Exception:
        return HTMLResponse(_POPUP_FAIL_HTML.format(provider="readai"))
    set_session_value(state, "readai_tokens", tokens)
    verified = _verify_readai(tokens.get("access_token", ""))
    return HTMLResponse(_POPUP_HTML.format(provider="readai", verified="true" if verified else "false"))


def _verify_readai(access_token: str) -> bool:
    try:
        resp = requests.get(
            "https://api.read.ai/v1/meetings",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 1},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


@router.get("/api/session/{session_id}/tokens")
def session_tokens(session_id: str):
    return {
        "google": get_token(session_id, "google") is not None,
        "notion": get_token(session_id, "notion") is not None,
        "readai": get_token(session_id, "readai") is not None,
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
