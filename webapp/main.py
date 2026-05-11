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


class PresignRequest(BaseModel):
    session_id: str
    filename: str
    content_type: str


def create_app() -> FastAPI:
    app = FastAPI(title="Entropy Onboarding")

    from .oauth import router as oauth_router
    app.include_router(oauth_router)

    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

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
        while True:
            body: dict = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
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
            data = resp.json()
            for row in data.get("results", []):
                rt = (row.get("properties", {})
                      .get("Account Manager", {})
                      .get("rich_text", []))
                if rt:
                    name = rt[0].get("plain_text", "").strip()
                    if name:
                        managers.add(name)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return {"managers": sorted(managers)}

    @app.post("/api/upload/presign")
    def upload_presign(req: PresignRequest):
        safe_name = re.sub(r"[^\w.\-]", "_", Path(req.filename).name)
        s3_key = f"uploads/{req.session_id}/{safe_name}"
        upload_url = s3.presign_upload(s3_key, req.content_type)
        return {"upload_url": upload_url, "s3_key": s3_key}

    return app
