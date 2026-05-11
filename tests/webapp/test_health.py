from starlette.testclient import TestClient
from webapp.main import create_app

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
