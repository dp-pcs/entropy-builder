import pytest
from starlette.testclient import TestClient
import webapp.session as session_module
from webapp.main import create_app

@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

@pytest.fixture(autouse=True)
def clear_sessions():
    session_module._store.clear()
    yield
    session_module._store.clear()
