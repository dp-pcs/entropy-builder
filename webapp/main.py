from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

_TEMPLATES_DIR = Path(__file__).parent / "templates"

def create_app() -> FastAPI:
    app = FastAPI(title="Entropy Onboarding")

    @app.get("/health")
    def health():
        return JSONResponse({"status": "ok"})

    return app
