# webapp/main.py
import re
from pathlib import Path
from typing import Optional
import requests
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from . import s3, db
from .auth import get_auth_user, delete_auth_token
from .config import settings
from .session import get_token, get_session_value

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


class PresignRequest(BaseModel):
    session_id: str
    filename: str
    content_type: str


class WizardSubmit(BaseModel):
    session_id: str
    user_role: str
    user_name: str
    account_manager_name: str
    team_members: list[str] = []
    s3_keys: list[str] = []
    interview_answers: dict = {}


_STATIC_DIR = Path(__file__).parent / "static"


_AUTH_COOKIE = "entropy_auth"


def _current_user(entropy_auth: Optional[str] = Cookie(default=None, alias=_AUTH_COOKIE)) -> Optional[dict]:
    if not entropy_auth:
        return None
    return get_auth_user(entropy_auth)


def _check_job_access(state: dict, user: Optional[dict], html: bool = False, job_id: str = "") -> None:
    """Raise HTTP error (or redirect for HTML pages) if the user doesn't own this job.
    Jobs without owner_sub (created before auth was added) are accessible to any authenticated user.
    """
    owner = state.get("owner_sub", "")
    if not owner:
        return  # pre-auth job — no restriction
    if user is None:
        if html:
            raise HTTPException(status_code=307, headers={"Location": "/oauth/google/return"})
        raise HTTPException(status_code=401, detail="Authentication required")
    if user["google_sub"] != owner:
        raise HTTPException(status_code=403, detail="Access denied")


def create_app() -> FastAPI:
    app = FastAPI(title="Entropy Onboarding")

    from .oauth import router as oauth_router
    app.include_router(oauth_router)

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    @app.get("/")
    def index(request: Request):
        return templates.TemplateResponse(request, "index.html")

    @app.get("/wizard")
    def wizard(request: Request):
        return templates.TemplateResponse(request, "wizard.html")

    @app.get("/health")
    def health():
        return JSONResponse({"status": "ok"})

    @app.get("/api/me")
    def me(user=Depends(_current_user)):
        if user is None:
            return JSONResponse({"authenticated": False})
        latest_job_id = None
        latest_job_created_at = None
        try:
            user_record = db.get_user(user["google_sub"])
            if user_record:
                latest_job_id = user_record.get("latest_job_id")
                jobs_list = user_record.get("jobs", [])
                match = next((j for j in jobs_list if j.get("job_id") == latest_job_id), None)
                if match:
                    latest_job_created_at = int(match.get("created_at", 0))
        except Exception:
            pass
        return {
            "authenticated": True,
            "email": user["email"],
            "name": user["name"],
            "latest_job_id": latest_job_id,
            "latest_job_created_at": latest_job_created_at,
        }

    @app.delete("/api/job/{job_id}")
    def delete_job(job_id: str, user=Depends(_current_user)):
        if not _UUID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job_id")
        state = s3.read_job_state(job_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Job not found")
        _check_job_access(state, user, html=False)
        s3.delete_job(job_id)
        if user:
            try:
                db.remove_job(user["google_sub"], job_id)
            except Exception:
                pass
        return {"ok": True}

    @app.post("/api/job/{job_id}/rebuild")
    def rebuild_job(job_id: str, user=Depends(_current_user)):
        """Re-run a previous job with the same config + uploaded inputs.

        Used when iterating on vault output without forcing the user to re-paste
        interview answers or re-upload files. Mints a fresh job_id; the original
        job's artifacts are preserved.
        """
        from . import jobs
        if not _UUID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job_id")
        state = s3.read_job_state(job_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Job not found")
        _check_job_access(state, user, html=False)
        config_dict = s3.read_job_config(job_id)
        if config_dict is None:
            raise HTTPException(status_code=410, detail="Original config no longer available")
        s3_keys = s3.read_job_inputs(job_id)
        if s3_keys is None:
            # Pre-rebuild-feature jobs didn't persist s3_keys; the user has to
            # rerun the wizard for those.
            raise HTTPException(
                status_code=409,
                detail="This job predates rebuild support. Start a new build from the wizard.",
            )
        owner_sub = state.get("owner_sub", "")
        new_job_id = jobs.create_job(config_dict, s3_keys, owner_sub=owner_sub)
        if owner_sub:
            try:
                db.record_job(owner_sub, new_job_id)
            except Exception:
                pass
        return {"job_id": new_job_id}

    @app.post("/api/logout")
    def logout(response: Response, entropy_auth: Optional[str] = Cookie(default=None, alias=_AUTH_COOKIE)):
        if entropy_auth:
            delete_auth_token(entropy_auth)
        response.delete_cookie(_AUTH_COOKIE, httponly=True, secure=True, samesite="lax")
        return {"ok": True}

    @app.get("/api/notion/account-managers")
    def notion_account_managers():
        access_token = settings.notion_token
        if not access_token:
            raise HTTPException(status_code=503, detail="Notion token not configured")
        managers: set[str] = set()
        cursor = None
        max_pages = 50  # safety guard against malformed has_more response
        for _ in range(max_pages):
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
                    raise HTTPException(status_code=401, detail="Notion token expired or invalid")
                raise HTTPException(status_code=502, detail="Notion API error")
            except requests.RequestException:
                raise HTTPException(status_code=504, detail="Notion API timeout")
            data = resp.json()
            for row in data.get("results", []):
                rt = (row.get("properties", {})
                      .get("Account Manager", {})
                      .get("rich_text", []))
                if rt:
                    name = rt[0].get("plain_text", "").strip()
                    if name:
                        managers.add(name)
            if not data.get("has_more") or not data.get("next_cursor"):
                break
            cursor = data.get("next_cursor")
        return {"managers": sorted(managers)}

    @app.post("/api/upload/presign")
    def upload_presign(req: PresignRequest):
        if not _UUID_RE.match(req.session_id):
            raise HTTPException(status_code=400, detail="Invalid session_id")
        safe_name = re.sub(r"[^\w.\-]", "_", Path(req.filename).name)
        if not safe_name or safe_name in (".", ".."):
            raise HTTPException(status_code=400, detail="Invalid filename")
        s3_key = f"uploads/{req.session_id}/{safe_name}"
        upload_url = s3.presign_upload(s3_key, req.content_type)
        return {"upload_url": upload_url, "s3_key": s3_key}

    @app.post("/api/wizard/submit")
    def wizard_submit(req: WizardSubmit):
        from . import jobs
        expected_prefix = f"uploads/{req.session_id}/"
        for key in req.s3_keys:
            if not key.startswith(expected_prefix):
                raise HTTPException(status_code=400, detail="Invalid s3_key: must be in your upload prefix")
        google_tokens = get_token(req.session_id, "google")
        if not google_tokens:
            raise HTTPException(status_code=400, detail="Google connection required")
        config_dict = {
            "user_name": req.user_name,
            "user_role": req.user_role,
            "account_manager_name": req.account_manager_name,
            "team_members": req.team_members,
            "notion_token": settings.notion_token,
            "notion_database_id": settings.notion_database_id,
            "google_credentials": {
                "access_token": google_tokens.get("access_token", ""),
                "refresh_token": google_tokens.get("refresh_token", ""),
                "client_id": google_tokens.get("client_id", settings.google_client_id),
                "client_secret": google_tokens.get("client_secret", settings.google_client_secret),
            },
            "readai_access_token": (get_token(req.session_id, "readai") or {}).get("access_token", ""),
            "readai_refresh_token": (get_token(req.session_id, "readai") or {}).get("refresh_token", ""),
            "readai_client_id": settings.readai_client_id,
            "fireworks_api_key": settings.fireworks_api_key,
            "truefoundry_api_key": settings.truefoundry_api_key,
            "interview_answers": req.interview_answers,
            "entropy_template_path": settings.entropy_template_path,
            "product_lines": [],
        }
        google_sub = get_session_value(req.session_id, "google_sub") or ""
        job_id = jobs.create_job(config_dict, req.s3_keys, owner_sub=google_sub)
        if google_sub:
            try:
                db.record_job(google_sub, job_id)
            except Exception:
                pass  # don't fail the job if DynamoDB is unavailable
        return {"job_id": job_id}

    @app.get("/api/job/{job_id}/status")
    def job_status(job_id: str, user=Depends(_current_user)):
        if not _UUID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job_id")
        state = s3.read_job_state(job_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Job not found")
        _check_job_access(state, user, html=False)
        result = dict(state)
        if state.get("vault_key"):
            result["vault_download_url"] = s3.presign_download(state["vault_key"])
        if state.get("claude_settings_key"):
            result["claude_settings_download_url"] = s3.presign_download(state["claude_settings_key"])
        return result

    @app.get("/job/{job_id}")
    def job_status_page(request: Request, job_id: str, user=Depends(_current_user)):
        if not _UUID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job_id")
        state = s3.read_job_state(job_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Job not found")
        _check_job_access(state, user, html=True, job_id=job_id)
        return templates.TemplateResponse(request, "status.html", {"job_id": job_id, "user": user})

    class GapPresignRequest(BaseModel):
        filename: str
        content_type: str

    @app.post("/api/job/{job_id}/gaps/presign")
    def gap_presign(job_id: str, req: GapPresignRequest, user=Depends(_current_user)):
        from . import jobs as _jobs
        if not _UUID_RE.match(job_id):
            raise HTTPException(status_code=400, detail="Invalid job_id")
        state = s3.read_job_state(job_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Job not found")
        _check_job_access(state, user, html=False)
        safe_name = re.sub(r"[^\w.\-]", "_", req.filename.rsplit("/", 1)[-1])
        s3_key = f"jobs/{job_id}/gaps/{safe_name}"
        upload_url = s3.presign_upload(s3_key, req.content_type)
        _jobs.update_job_state(job_id, gap_s3_keys=list(state.get("gap_s3_keys", [])) + [s3_key])
        return {"upload_url": upload_url, "s3_key": s3_key}

    return app


app = create_app()
