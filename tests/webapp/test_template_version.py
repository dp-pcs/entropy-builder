"""Tests for /api/template/version and /api/migrations/{version} endpoints.

Both are PUBLIC (no auth) — see [[entropy-migration-auth]] memory.
"""
import json
from pathlib import Path

import pytest


@pytest.fixture
def template_fixture(tmp_path, mocker):
    """Build a fake entropy-template/ with TEMPLATE_VERSION.json + .changelog/."""
    template = tmp_path / "entropy-template"
    template.mkdir()
    (template / "TEMPLATE_VERSION.json").write_text(json.dumps({
        "version": "1.2.0",
        "updated": "2026-05-20",
        "versions": {
            "core": "1.2.0",
            "role:ic-sales": "1.0.3",
        },
        "history": [],
    }, indent=2))
    (template / ".changelog" / "core").mkdir(parents=True)
    (template / ".changelog" / "core" / "v1.2.0.md").write_text(
        "---\nversion: 1.2.0\ntype: minor\n---\n\nCore change.\n"
    )
    (template / ".changelog" / "role-ic-sales").mkdir(parents=True)
    (template / ".changelog" / "role-ic-sales" / "v1.0.3.md").write_text(
        "---\nversion: 1.0.3\nscope: role:ic-sales\ntype: minor\n---\n\nSales change.\n"
    )
    mocker.patch("webapp.main.settings.entropy_template_path", str(template))
    return template


def test_version_endpoint_returns_multi_axis_map(client, template_fixture):
    resp = client.get("/api/template/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["core_version"] == "1.2.0"
    assert body["versions"] == {"core": "1.2.0", "role:ic-sales": "1.0.3"}
    assert body["updated"] == "2026-05-20"


def test_version_endpoint_with_role_returns_role_pack(client, template_fixture):
    resp = client.get("/api/template/version?role=ic-sales")
    assert resp.status_code == 200
    body = resp.json()
    assert body["core_version"] == "1.2.0"
    assert body["role_pack"] == {"role": "ic-sales", "version": "1.0.3"}


def test_version_endpoint_unknown_role_returns_null_pack(client, template_fixture):
    resp = client.get("/api/template/version?role=founder")
    assert resp.status_code == 200
    assert resp.json()["role_pack"] is None


def test_version_endpoint_rejects_invalid_role(client, template_fixture):
    resp = client.get("/api/template/version?role=BAD..NAME")
    assert resp.status_code == 400


def test_version_endpoint_503_when_unconfigured(client, mocker):
    mocker.patch("webapp.main.settings.entropy_template_path", "")
    resp = client.get("/api/template/version")
    assert resp.status_code == 503


def test_migrations_returns_core_payload(client, template_fixture):
    resp = client.get("/api/migrations/1.2.0")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert "Core change." in resp.text


def test_migrations_returns_role_scoped_payload(client, template_fixture):
    resp = client.get("/api/migrations/1.0.3?scope=role:ic-sales")
    assert resp.status_code == 200
    assert "Sales change." in resp.text


def test_migrations_404_for_missing_version(client, template_fixture):
    resp = client.get("/api/migrations/9.9.9")
    assert resp.status_code == 404


def test_migrations_rejects_invalid_version(client, template_fixture):
    resp = client.get("/api/migrations/not-a-version")
    assert resp.status_code == 400


def test_migrations_rejects_invalid_scope(client, template_fixture):
    resp = client.get("/api/migrations/1.2.0?scope=evil/../path")
    assert resp.status_code == 400


def test_migrations_no_auth_required(client, template_fixture):
    """Confirm the endpoint is genuinely public — no cookie sent."""
    resp = client.get("/api/migrations/1.2.0", cookies={})
    assert resp.status_code == 200


def test_archive_endpoint_returns_tarball(client, template_fixture):
    import io
    import tarfile

    (template_fixture / "_skills" / "intro.md").parent.mkdir(parents=True)
    (template_fixture / "_skills" / "intro.md").write_text("# intro\n")

    resp = client.get("/api/template/archive")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/gzip"
    assert "attachment" in resp.headers["content-disposition"]

    with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
        names = set(tar.getnames())
    assert "TEMPLATE_VERSION.json" in names
    assert ".changelog/core/v1.2.0.md" in names
    assert "_skills/intro.md" in names


def test_archive_endpoint_excludes_junk(client, template_fixture):
    import io
    import tarfile

    (template_fixture / ".DS_Store").write_bytes(b"junk")
    (template_fixture / "_skills").mkdir()
    (template_fixture / "_skills" / "__pycache__").mkdir()
    (template_fixture / "_skills" / "__pycache__" / "x.pyc").write_bytes(b"junk")

    resp = client.get("/api/template/archive")
    with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
        names = set(tar.getnames())
    assert not any(".DS_Store" in n or "__pycache__" in n for n in names)


def test_archive_endpoint_503_when_unconfigured(client, mocker):
    mocker.patch("webapp.main.settings.entropy_template_path", "")
    resp = client.get("/api/template/archive")
    assert resp.status_code == 503
