"""Tests for pipeline/migrations/applier.py — fixture-driven.

Builds a fake `local-source` checkout (the "template" side) and a vault dir
under tmp_path, drives apply() in --local-source mode, and asserts:
  - multi-version semver replay lands vault_version.json at latest
  - conflict invariants per handler (preserve local, write .new sidecar)
  - dry-run touches no files and writes no version bump
  - wikilink rewrite happens on rename and is counted in the report
  - manifest mode tightens delete/patch semantics (precise vs. conservative)
"""
import io
import json
import tarfile
from pathlib import Path

import pytest

from pipeline.migrations import applier, client, report
from pipeline.migrations.paths import sha256_of_path


# -----------------------------------------------------------------------------
# Fixture builders
# -----------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _changes_file(local_source: Path, version: str, changes: list[dict], scope: str = "core") -> Path:
    scope_dir = scope.replace(":", "-")
    path = local_source / ".changelog" / scope_dir / f"v{version}.md"
    frontmatter = {
        "version": version,
        "type": "minor",
        "scope": scope,
        "summary": f"test v{version}",
        "changes": changes,
    }
    import yaml
    text = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\nbody\n"
    _write(path, text)
    return path


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    v.mkdir()
    _write(v / "vault_version.json", json.dumps({
        "template_version": "1.0.0",
        "update_check_url": "https://example.test/api/template/version",
    }))
    _write(v / "Portfolio Brain" / "Customers" / "Acme.md", "# Acme\n\nLinked: [[Portfolio Brain/_skills/old-skill]]\n")
    _write(v / "Portfolio Brain" / "_skills" / "old-skill.md", "# Old skill\n")
    return v


@pytest.fixture
def local_source(tmp_path: Path) -> Path:
    s = tmp_path / "local-source"
    s.mkdir()
    _write(s / "TEMPLATE_VERSION.json", json.dumps({
        "version": "1.0.0",
        "versions": {"core": "1.0.0"},
    }))
    # Mirror the vault's starting state so content_patch / delete have a
    # plausible baseline.
    _write(s / "Portfolio Brain" / "Customers" / "Acme.md", "# Acme\n\nLinked: [[Portfolio Brain/_skills/old-skill]]\n")
    _write(s / "Portfolio Brain" / "_skills" / "old-skill.md", "# Old skill\n")
    return s


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_no_op_when_vault_already_at_latest(vault, local_source):
    rpt = applier.apply(vault, local_source=local_source)
    assert rpt.to_version == "1.0.0"
    assert rpt.from_version == "1.0.0"
    assert all(r.status == "noop" for r in rpt.results)


def test_multi_version_semver_replay_bumps_vault_version(vault, local_source):
    # v1.1.0 adds skill A; v1.2.0 adds skill B. Order matters: replay must apply
    # both in semver order and bump vault_version to the highest.
    _write(local_source / "Portfolio Brain" / "_skills" / "skill-a.md", "# A\n")
    _write(local_source / "Portfolio Brain" / "_skills" / "skill-b.md", "# B\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/skill-a.md", "rationale": "add A"},
    ])
    _changes_file(local_source, "1.2.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/skill-b.md", "rationale": "add B"},
    ])

    rpt = applier.apply(vault, local_source=local_source)

    assert rpt.to_version == "1.2.0"
    assert rpt.from_version == "1.0.0"
    versions_applied = {r.version for r in rpt.applied}
    assert versions_applied == {"1.1.0", "1.2.0"}
    assert (vault / "Portfolio Brain" / "_skills" / "skill-a.md").read_text() == "# A\n"
    assert (vault / "Portfolio Brain" / "_skills" / "skill-b.md").read_text() == "# B\n"
    vv = json.loads((vault / "vault_version.json").read_text())
    assert vv["template_version"] == "1.2.0"


def test_dry_run_writes_no_files_and_no_version_bump(vault, local_source):
    _write(local_source / "Portfolio Brain" / "_skills" / "new-skill.md", "# New\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/new-skill.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source, dry_run=True)

    assert rpt.dry_run is True
    assert not (vault / "Portfolio Brain" / "_skills" / "new-skill.md").exists()
    vv = json.loads((vault / "vault_version.json").read_text())
    assert vv["template_version"] == "1.0.0"  # unchanged


def test_add_file_collision_preserves_local_and_writes_dot_new(vault, local_source):
    # Local user already has a file at the path with different content.
    _write(vault / "Portfolio Brain" / "_skills" / "new-skill.md", "# my own version\n")
    _write(local_source / "Portfolio Brain" / "_skills" / "new-skill.md", "# template version\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/new-skill.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source)

    local = (vault / "Portfolio Brain" / "_skills" / "new-skill.md").read_text()
    assert local == "# my own version\n"
    sidecar = vault / "Portfolio Brain" / "_skills" / "new-skill.md.new"
    assert sidecar.exists()
    assert sidecar.read_text() == "# template version\n"
    assert any(r.status == "conflict" for r in rpt.results)


def test_content_patch_diverged_writes_dot_new_keeps_local(vault, local_source):
    # User edited Acme.md after build (so it diverges from template's old version).
    _write(vault / "Portfolio Brain" / "Customers" / "Acme.md", "# Acme\n\nmy notes\n")
    # New template content for v1.1.0 patches Acme.md to something else.
    _write(local_source / "Portfolio Brain" / "Customers" / "Acme.md", "# Acme\n\ntemplate-updated\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "content_patch", "path": "Portfolio Brain/Customers/Acme.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source)

    local = (vault / "Portfolio Brain" / "Customers" / "Acme.md").read_text()
    assert local == "# Acme\n\nmy notes\n"
    sidecar = vault / "Portfolio Brain" / "Customers" / "Acme.md.new"
    assert sidecar.read_text() == "# Acme\n\ntemplate-updated\n"
    assert [r for r in rpt.results if r.status == "conflict"]


def test_content_patch_clean_overwrite_with_manifest(vault, local_source):
    # Establish a vault-side manifest with the *current* file hash so the
    # applier recognises the local copy as "unchanged since template".
    acme = vault / "Portfolio Brain" / "Customers" / "Acme.md"
    _write(vault / applier.VAULT_MANIFEST_FILE, json.dumps({
        "template_version": "1.0.0",
        "files": {
            "Portfolio Brain/Customers/Acme.md": {
                "source_sha256": sha256_of_path(acme),
                "last_updated_version": "1.0.0",
            },
        },
    }))
    _write(local_source / "Portfolio Brain" / "Customers" / "Acme.md", "# Acme\n\ntemplate v2\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "content_patch", "path": "Portfolio Brain/Customers/Acme.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source)

    # Clean overwrite — no sidecar, content matches template.
    assert acme.read_text() == "# Acme\n\ntemplate v2\n"
    assert not (vault / "Portfolio Brain" / "Customers" / "Acme.md.new").exists()
    assert any(r.handler == "content_patch" and r.status == "applied" for r in rpt.results)


def test_delete_file_preserved_without_manifest(vault, local_source):
    _changes_file(local_source, "1.1.0", [
        {"type": "delete_file", "path": "Portfolio Brain/_skills/old-skill.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source)

    # Without a vault manifest, conservative-preserve keeps the file.
    assert (vault / "Portfolio Brain" / "_skills" / "old-skill.md").exists()
    assert any(r.handler == "delete_file" and r.status == "conflict" for r in rpt.results)


def test_delete_file_with_matching_manifest_hash_deletes(vault, local_source):
    skill = vault / "Portfolio Brain" / "_skills" / "old-skill.md"
    _write(vault / applier.VAULT_MANIFEST_FILE, json.dumps({
        "template_version": "1.0.0",
        "files": {
            "Portfolio Brain/_skills/old-skill.md": {
                "source_sha256": sha256_of_path(skill),
                "last_updated_version": "1.0.0",
            },
        },
    }))
    _changes_file(local_source, "1.1.0", [
        {"type": "delete_file", "path": "Portfolio Brain/_skills/old-skill.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source)

    assert not skill.exists()
    assert any(r.handler == "delete_file" and r.status == "applied" for r in rpt.results)


def test_rename_moves_file_and_rewrites_wikilinks(vault, local_source):
    _changes_file(local_source, "1.1.0", [
        {
            "type": "rename",
            "from": "Portfolio Brain/_skills/old-skill.md",
            "to": "Portfolio Brain/_skills/new-skill.md",
            "rationale": "rename",
        },
    ])

    rpt = applier.apply(vault, local_source=local_source)

    assert not (vault / "Portfolio Brain" / "_skills" / "old-skill.md").exists()
    assert (vault / "Portfolio Brain" / "_skills" / "new-skill.md").exists()
    # Wikilink rewrite in Acme.md.
    acme = (vault / "Portfolio Brain" / "Customers" / "Acme.md").read_text()
    assert "[[Portfolio Brain/_skills/new-skill]]" in acme
    assert "[[Portfolio Brain/_skills/old-skill]]" not in acme
    # Report counts the rewrite.
    renames = [r for r in rpt.results if r.handler == "rename"]
    assert renames and renames[0].links_rewritten >= 1


def test_rename_collision_when_destination_exists_keeps_both(vault, local_source):
    _write(vault / "Portfolio Brain" / "_skills" / "new-skill.md", "# user-created collision\n")
    _changes_file(local_source, "1.1.0", [
        {
            "type": "rename",
            "from": "Portfolio Brain/_skills/old-skill.md",
            "to": "Portfolio Brain/_skills/new-skill.md",
            "rationale": "rename",
        },
    ])

    rpt = applier.apply(vault, local_source=local_source)

    assert (vault / "Portfolio Brain" / "_skills" / "old-skill.md").exists()
    assert (vault / "Portfolio Brain" / "_skills" / "new-skill.md").read_text() == "# user-created collision\n"
    assert any(r.handler == "rename" and r.status == "conflict" for r in rpt.results)


def test_report_written_under_vault_outputs(vault, local_source):
    _write(local_source / "Portfolio Brain" / "_skills" / "new-skill.md", "# New\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/new-skill.md", "rationale": "x"},
    ])

    rpt = applier.apply(vault, local_source=local_source)
    written = report.write_report(vault, rpt)
    assert written.exists()
    assert "Migration report" in written.read_text()
    assert written.parent.name == "outputs"


# -----------------------------------------------------------------------------
# HTTP mode — orchestrator fetches /api/template/archive once, extracts to a
# temp dir, then drives the rest with that synthetic local_source.
# -----------------------------------------------------------------------------

def _tar_gz_of(root: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for p in sorted(root.rglob("*")):
            tar.add(p, arcname=str(p.relative_to(root)), recursive=False)
    return buf.getvalue()


def test_http_mode_extracts_archive_and_applies(vault, local_source, mocker):
    """HTTP mode: applier fetches archive, extracts, applies the same as --local-source."""
    _write(local_source / "Portfolio Brain" / "_skills" / "skill-a.md", "# A\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/skill-a.md", "rationale": "add A"},
    ])
    archive_bytes = _tar_gz_of(local_source)
    fetch = mocker.patch("pipeline.migrations.client.fetch_template_archive", return_value=archive_bytes)

    rpt = applier.apply(vault, local_source=None, base_url="https://test.invalid")

    fetch.assert_called_once()
    assert rpt.to_version == "1.1.0"
    assert (vault / "Portfolio Brain" / "_skills" / "skill-a.md").read_text() == "# A\n"


def test_http_mode_replays_multiple_versions_from_archive(vault, local_source, mocker):
    """Confirms the archive's .changelog/ enables full multi-version replay over HTTP."""
    _write(local_source / "Portfolio Brain" / "_skills" / "skill-a.md", "# A\n")
    _write(local_source / "Portfolio Brain" / "_skills" / "skill-b.md", "# B\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/skill-a.md", "rationale": "add A"},
    ])
    _changes_file(local_source, "1.2.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/skill-b.md", "rationale": "add B"},
    ])
    archive_bytes = _tar_gz_of(local_source)
    mocker.patch("pipeline.migrations.client.fetch_template_archive", return_value=archive_bytes)

    rpt = applier.apply(vault, local_source=None, base_url="https://test.invalid")

    assert rpt.to_version == "1.2.0"
    assert (vault / "Portfolio Brain" / "_skills" / "skill-a.md").exists()
    assert (vault / "Portfolio Brain" / "_skills" / "skill-b.md").exists()


def test_http_mode_cleans_up_tempdir(vault, local_source, mocker):
    """The TemporaryDirectory must be gone after apply() returns."""
    _write(local_source / "Portfolio Brain" / "_skills" / "skill-a.md", "# A\n")
    _changes_file(local_source, "1.1.0", [
        {"type": "add_file", "path": "Portfolio Brain/_skills/skill-a.md", "rationale": "x"},
    ])
    archive_bytes = _tar_gz_of(local_source)
    mocker.patch("pipeline.migrations.client.fetch_template_archive", return_value=archive_bytes)

    extracted_dirs: list[Path] = []
    real_extract = client.extract_template_archive

    def spy_extract(data, dest):
        extracted_dirs.append(dest)
        return real_extract(data, dest)

    mocker.patch("pipeline.migrations.client.extract_template_archive", side_effect=spy_extract)

    applier.apply(vault, local_source=None, base_url="https://test.invalid")

    assert extracted_dirs and not extracted_dirs[0].exists(), "tempdir should be cleaned up"


def test_extract_archive_rejects_path_traversal(tmp_path):
    """Defense against malicious tarballs."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="../escape.txt")
        info.size = 4
        tar.addfile(info, io.BytesIO(b"oops"))

    with pytest.raises(client.MigrationClientError, match="unsafe member path"):
        client.extract_template_archive(buf.getvalue(), tmp_path / "out")
