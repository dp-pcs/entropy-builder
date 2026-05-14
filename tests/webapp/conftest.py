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
    """Reset between tests. Sessions used to live in an in-memory _store dict
    but moved to a DynamoDB-backed _table(); the in-memory clear path is now
    a best-effort no-op so tests don't break when boto3 isn't configured."""
    legacy_store = getattr(session_module, "_store", None)
    if legacy_store is not None:
        legacy_store.clear()
    yield
    if legacy_store is not None:
        legacy_store.clear()
