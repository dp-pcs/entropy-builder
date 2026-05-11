# webapp/main.py
import re
from pathlib import Path
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from . import s3
from .config import settings
from .session import get_token

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


class PresignRequest(BaseModel):
    session_id: str
    filename: str
    content_type: str


def create_app() -> FastAPI:
    app = FastAPI(title="Entropy Onboarding")

    from .oauth import router as oauth_router
    app.include_router(oauth_router)

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

    @app.get("/api/notion/account-managers")
    def notion_account_managers(session_id: str):
        tokens = get_token(session_id, "notion")
        if not tokens:
            raise HTTPException(status_code=401, detail="Notion not connected")
        access_token = tokens["access_token"]
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

    return app
