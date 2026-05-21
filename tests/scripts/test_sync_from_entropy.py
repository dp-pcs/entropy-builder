"""Tests for scripts/sync_from_entropy.py — fixture-driven.

Each test builds a fake Jay repo (real git init, real commits) and a fake
entropy-template/ directory under tmp_path, monkeypatches the sync module's
path globals, and runs `run()` directly.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Allow `import sync_from_entropy` from scripts/
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import sync_from_entropy as sync  # noqa: E402


# -----------------------------------------------------------------------------
# Fixture builders
# -----------------------------------------------------------------------------

def _init_git(repo_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)


def _commit_all(repo_path: Path, msg: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=repo_path, check=True)
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def _sha256_str(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


@pytest.fixture
def fake_repos(tmp_path, monkeypatch):
    """Build (jay_repo, template_root) with one tracked file each + a wired manifest."""
    jay = tmp_path / "jay"
    jay.mkdir()
    (jay / "Portfolio Brain" / "_skills").mkdir(parents=True)
    (jay / "Portfolio Brain" / "_analytics").mkdir(parents=True)
    skill = jay / "Portfolio Brain" / "_skills" / "ingestion.md"
    skill.write_text("# Ingestion\n\nOriginal content.\n")
    analytics = jay / "Portfolio Brain" / "_analytics" / "metrics.md"
    analytics.write_text("# Metrics\n")
    rules = jay / "Portfolio Brain" / "Company-Rules.md"
    rules.write_text("# Rules\n")
    _init_git(jay)
    base_sha = _commit_all(jay, "initial")

    template = tmp_path / "entropy-template"
    template.mkdir()
    (template / "Portfolio Brain" / "_skills").mkdir(parents=True)
    (template / "Portfolio Brain" / "_analytics").mkdir(parents=True)
    (template / "Portfolio Brain" / "_skills" / "ingestion.md").write_text("# Ingestion\n\nOriginal content.\n")
    (template / "Portfolio Brain" / "_analytics" / "metrics.md").write_text("# Metrics\n")
    (template / "Portfolio Brain" / "Company-Rules.md").write_text("# Rules\n")

    manifest = {
        "schema_version": 1,
        "source_repo": "jaykhalife/entropy",
        "source_branch": "main",
        "last_synced_commit": base_sha,
        "last_synced_at": "2026-05-13T00:00:00Z",
        "tracked_paths": [
            "Portfolio Brain/_skills/",
            "Portfolio Brain/_analytics/",
            "Portfolio Brain/Company-Rules.md",
        ],
        "files": {
            "Portfolio Brain/_skills/ingestion.md": {
                "source_sha256": _sha256_str("# Ingestion\n\nOriginal content.\n"),
                "dest_path_in_template": "entropy-template/Portfolio Brain/_skills/ingestion.md",
                "first_seen_version": "bootstrap",
                "last_updated_version": "bootstrap",
            },
            "Portfolio Brain/_analytics/metrics.md": {
                "source_sha256": _sha256_str("# Metrics\n"),
                "dest_path_in_template": "entropy-template/Portfolio Brain/_analytics/metrics.md",
                "first_seen_version": "bootstrap",
                "last_updated_version": "bootstrap",
            },
            "Portfolio Brain/Company-Rules.md": {
                "source_sha256": _sha256_str("# Rules\n"),
                "dest_path_in_template": "entropy-template/Portfolio Brain/Company-Rules.md",
                "first_seen_version": "bootstrap",
                "last_updated_version": "bootstrap",
            },
        },
        "ingested_changes": [],
    }
    (template / ".jay-sync-manifest.json").write_text(json.dumps(manifest, indent=2))
    (template / "TEMPLATE_VERSION.json").write_text(json.dumps({
        "version": "1.0.0",
        "updated": "2026-05-01",
        "history": [],
    }, indent=2))

    monkeypatch.setattr(sync, "TEMPLATE_ROOT", template)
    monkeypatch.setattr(sync, "MANIFEST_PATH", template / ".jay-sync-manifest.json")
    monkeypatch.setattr(sync, "VERSION_FILE", template / "TEMPLATE_VERSION.json")
    return jay, template


def _write_changes_file(jay: Path, filename: str, content: str) -> None:
    changes_dir = jay / "CHANGES"
    changes_dir.mkdir(exist_ok=True)
    (changes_dir / filename).write_text(content)


# -----------------------------------------------------------------------------
# Behavior tests
# -----------------------------------------------------------------------------

def test_no_new_commits_returns_2(fake_repos, capsys):
    jay, template = fake_repos
    # last_synced_commit == HEAD already → nothing to do
    result = sync.run(jay)
    assert result == 2


def test_drift_only_returns_pr_with_drift_section(fake_repos, capsys):
    jay, template = fake_repos
    # Modify a tracked file in Jay's repo without writing a CHANGES entry
    (jay / "Portfolio Brain" / "Company-Rules.md").write_text("# Rules\n\nNew section.\n")
    _commit_all(jay, "edit company rules")

    result = sync.run(jay)
    assert result == 0
    out = capsys.readouterr().out
    assert "drift detected" in out.lower()
    assert "Company-Rules.md" in out


def test_add_file_handler_copies_and_updates_manifest(fake_repos, capsys):
    jay, template = fake_repos
    new_skill = jay / "Portfolio Brain" / "_skills" / "new-skill.md"
    new_skill.write_text("# New Skill\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Add new-skill
changes:
  - type: add_file
    path: Portfolio Brain/_skills/new-skill.md
    rationale: "New workflow"
---

Added new-skill.
""")
    _commit_all(jay, "add new skill")

    assert sync.run(jay) == 0

    dest = template / "Portfolio Brain" / "_skills" / "new-skill.md"
    assert dest.exists()
    assert dest.read_text() == "# New Skill\n"

    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    assert "Portfolio Brain/_skills/new-skill.md" in manifest["files"]
    assert manifest["ingested_changes"][0]["version"] == "1.1.0"

    version_data = json.loads((template / "TEMPLATE_VERSION.json").read_text())
    assert version_data["version"] == "1.1.0"
    assert version_data["history"][0]["version"] == "1.1.0"

    out = capsys.readouterr().out
    assert "v1.1.0" in out
    assert "added Portfolio Brain/_skills/new-skill.md" in out


def test_rename_handler_moves_file_and_rewrites_manifest_paths(fake_repos, capsys):
    jay, template = fake_repos
    # Stage the rename in Jay's repo too so drift check passes
    (jay / "Portfolio Brain" / "_skills" / "renamed.md").write_text("# Ingestion\n\nOriginal content.\n")
    (jay / "Portfolio Brain" / "_skills" / "ingestion.md").unlink()
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Rename ingestion.md
changes:
  - type: rename
    from: Portfolio Brain/_skills/ingestion.md
    to: Portfolio Brain/_skills/renamed.md
    rationale: "Better name"
---

Renamed.
""")
    _commit_all(jay, "rename")

    assert sync.run(jay) == 0
    assert (template / "Portfolio Brain" / "_skills" / "renamed.md").exists()
    assert not (template / "Portfolio Brain" / "_skills" / "ingestion.md").exists()

    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    assert "Portfolio Brain/_skills/renamed.md" in manifest["files"]
    assert "Portfolio Brain/_skills/ingestion.md" not in manifest["files"]


def test_delete_file_handler_removes_from_template_and_manifest(fake_repos, capsys):
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "ingestion.md").unlink()
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Remove deprecated skill
changes:
  - type: delete_file
    path: Portfolio Brain/_skills/ingestion.md
    rationale: "Replaced by triage"
---

Removed.
""")
    _commit_all(jay, "delete ingestion")

    assert sync.run(jay) == 0
    assert not (template / "Portfolio Brain" / "_skills" / "ingestion.md").exists()
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    assert "Portfolio Brain/_skills/ingestion.md" not in manifest["files"]


def test_content_patch_handler_overwrites_template(fake_repos, capsys):
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "Company-Rules.md").write_text("# Rules\n\nUpdated.\n")
    _write_changes_file(jay, "v1.0.1.md", """---
version: 1.0.1
date: 2026-05-14
type: patch
summary: Clarify Tier-2 rules
changes:
  - type: content_patch
    path: Portfolio Brain/Company-Rules.md
    rationale: "Clarified escalation"
---

Updated wording.
""")
    _commit_all(jay, "edit rules")

    assert sync.run(jay) == 0
    assert (template / "Portfolio Brain" / "Company-Rules.md").read_text() == "# Rules\n\nUpdated.\n"


def test_structure_split_records_but_does_not_move_template_files(fake_repos, capsys):
    """structure_split applies to user vaults, not the template; template entry is recorded only."""
    jay, template = fake_repos
    _write_changes_file(jay, "v2.0.0.md", """---
version: 2.0.0
date: 2026-05-14
type: major
summary: Split Meetings into Internal/External
changes:
  - type: structure_split
    from: Portfolio Brain/Meetings/
    to:
      - Portfolio Brain/Meetings/Internal/
      - Portfolio Brain/Meetings/External/
    classifier:
      method: participant_domain_majority
      params:
        internal_domains: [trilogy.com]
        threshold: 0.5
        default: External
    rationale: "Surface customer meetings"
---

Split.
""")
    _commit_all(jay, "split meetings")

    assert sync.run(jay) == 0
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    assert manifest["ingested_changes"][0]["version"] == "2.0.0"

    version_data = json.loads((template / "TEMPLATE_VERSION.json").read_text())
    assert version_data["history"][0]["changes"][0]["type"] == "structure_split"


# -----------------------------------------------------------------------------
# Validation tests
# -----------------------------------------------------------------------------

def test_invalid_handler_type_raises(fake_repos):
    jay, _ = fake_repos
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Bogus
changes:
  - type: teleport
    path: foo
    rationale: r
---

Bad.
""")
    _commit_all(jay, "bad change")

    with pytest.raises(sync.ValidationError, match="unknown handler"):
        sync.run(jay)


def test_filename_version_mismatch_raises(fake_repos):
    jay, _ = fake_repos
    _write_changes_file(jay, "v1.1.0.md", """---
version: 9.9.9
date: 2026-05-14
type: minor
summary: x
changes:
  - type: add_file
    path: Portfolio Brain/_skills/x.md
    rationale: r
---
""")
    _commit_all(jay, "mismatched version")

    with pytest.raises(sync.ValidationError, match="does not match filename"):
        sync.run(jay)


def test_structure_split_unknown_classifier_raises(fake_repos):
    jay, _ = fake_repos
    _write_changes_file(jay, "v2.0.0.md", """---
version: 2.0.0
date: 2026-05-14
type: major
summary: x
changes:
  - type: structure_split
    from: Portfolio Brain/Meetings/
    to: [Portfolio Brain/Meetings/A/, Portfolio Brain/Meetings/B/]
    classifier:
      method: tarot_card_draw
    rationale: r
---
""")
    _commit_all(jay, "bad classifier")

    with pytest.raises(sync.ValidationError, match="unknown classifier"):
        sync.run(jay)


def test_excluded_add_file_is_skipped_and_recorded(fake_repos, capsys):
    """add_file on an excluded path: no template copy, no manifest['files'] entry,
    but the version IS recorded as ingested so we don't re-process every run."""
    jay, template = fake_repos
    # Add an exclusion to the manifest
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    manifest["excluded_paths"] = ["Portfolio Brain/_skills/internal-only.md"]
    (template / ".jay-sync-manifest.json").write_text(json.dumps(manifest, indent=2))

    (jay / "Portfolio Brain" / "_skills" / "internal-only.md").write_text("# Internal\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Add internal-only skill
changes:
  - type: add_file
    path: Portfolio Brain/_skills/internal-only.md
    rationale: "Jay-only skill; not for end users"
---

Excluded from user vaults.
""")
    _commit_all(jay, "add internal skill")

    assert sync.run(jay) == 0

    # Template did NOT get the file
    assert not (template / "Portfolio Brain" / "_skills" / "internal-only.md").exists()

    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    # File is NOT in manifest['files'] (we don't track excluded files)
    assert "Portfolio Brain/_skills/internal-only.md" not in manifest["files"]
    # But the version IS recorded so we don't re-process
    assert manifest["ingested_changes"][0]["version"] == "1.1.0"

    # PR body mentions the skip
    out = capsys.readouterr().out
    assert "skipped (excluded)" in out
    assert "Portfolio Brain/_skills/internal-only.md" in out


def test_excluded_path_does_not_trigger_drift(fake_repos, capsys):
    """A new file Jay added in a tracked-but-excluded location should NOT show
    up as drift."""
    jay, template = fake_repos
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    manifest["excluded_paths"] = ["Portfolio Brain/_skills/internal-only.md"]
    (template / ".jay-sync-manifest.json").write_text(json.dumps(manifest, indent=2))

    (jay / "Portfolio Brain" / "_skills" / "internal-only.md").write_text("# Internal\n")
    _commit_all(jay, "add internal skill without CHANGES entry")

    result = sync.run(jay)
    # Either 0 (drift report) or 2 (nothing to do). Should NOT be drift on the
    # excluded file specifically.
    out = capsys.readouterr().out
    assert "internal-only.md" not in out


def test_rename_across_exclusion_boundary_raises(fake_repos):
    """Rename from excluded -> tracked (or vice versa) needs human handling."""
    jay, template = fake_repos
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    manifest["excluded_paths"] = ["Portfolio Brain/_skills/secret.md"]
    (template / ".jay-sync-manifest.json").write_text(json.dumps(manifest, indent=2))

    # Try renaming a tracked file INTO the excluded slot
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Bad rename across boundary
changes:
  - type: rename
    from: Portfolio Brain/_skills/ingestion.md
    to: Portfolio Brain/_skills/secret.md
    rationale: "shouldn't be allowed"
---
""")
    _commit_all(jay, "bad rename")

    with pytest.raises(sync.ValidationError, match="exclusion boundary"):
        sync.run(jay)


def test_dry_run_does_not_write_files(fake_repos, capsys):
    jay, template = fake_repos
    new_skill = jay / "Portfolio Brain" / "_skills" / "dry.md"
    new_skill.write_text("# Dry\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: x
changes:
  - type: add_file
    path: Portfolio Brain/_skills/dry.md
    rationale: r
---
""")
    _commit_all(jay, "add")

    before_manifest = (template / ".jay-sync-manifest.json").read_text()
    assert sync.run(jay, dry_run=True) == 0
    assert not (template / "Portfolio Brain" / "_skills" / "dry.md").exists()
    assert (template / ".jay-sync-manifest.json").read_text() == before_manifest


# -----------------------------------------------------------------------------
# Scope (multi-axis versioning) tests — see [[entropy-versioning]] memory
# -----------------------------------------------------------------------------

def test_scope_defaults_to_core_when_omitted(fake_repos, capsys):
    """Backward-compat: CHANGES files without a scope field default to 'core'."""
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "x.md").write_text("# X\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: no scope declared
changes:
  - type: add_file
    path: Portfolio Brain/_skills/x.md
    rationale: r
---
""")
    _commit_all(jay, "add")

    assert sync.run(jay) == 0
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    assert manifest["ingested_changes"][0]["scope"] == "core"
    version_data = json.loads((template / "TEMPLATE_VERSION.json").read_text())
    assert version_data["history"][0]["scope"] == "core"


def test_scope_role_is_accepted_and_recorded(fake_repos, capsys):
    """role:<name> scope is valid and flows into manifest + version history."""
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "sales-only.md").write_text("# Sales\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
scope: role:ic-sales
summary: Sales-only skill
changes:
  - type: add_file
    path: Portfolio Brain/_skills/sales-only.md
    rationale: "Sales workflow"
---
""")
    _commit_all(jay, "add sales skill")

    assert sync.run(jay) == 0
    manifest = json.loads((template / ".jay-sync-manifest.json").read_text())
    assert manifest["ingested_changes"][0]["scope"] == "role:ic-sales"
    out = capsys.readouterr().out
    assert "scope: role:ic-sales" in out


def test_changes_file_archived_to_changelog_core(fake_repos, capsys):
    """Processed CHANGES files are copied into entropy-template/.changelog/core/."""
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "y.md").write_text("# Y\n")
    changes_content = """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: Archive me
changes:
  - type: add_file
    path: Portfolio Brain/_skills/y.md
    rationale: "for archival test"
---

Prose body that must survive archival.
"""
    _write_changes_file(jay, "v1.1.0.md", changes_content)
    _commit_all(jay, "add y")

    assert sync.run(jay) == 0
    archived = template / ".changelog" / "core" / "v1.1.0.md"
    assert archived.exists(), "CHANGES file should be archived under .changelog/core/"
    assert archived.read_text() == changes_content


def test_role_scoped_changes_archived_under_role_subdir(fake_repos, capsys):
    """role:ic-sales scope buckets archive into .changelog/role-ic-sales/."""
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "sales.md").write_text("# Sales\n")
    _write_changes_file(jay, "v1.2.0.md", """---
version: 1.2.0
date: 2026-05-14
type: minor
scope: role:ic-sales
summary: Sales pack update
changes:
  - type: add_file
    path: Portfolio Brain/_skills/sales.md
    rationale: "sales-only"
---
""")
    _commit_all(jay, "sales pack")

    assert sync.run(jay) == 0
    archived = template / ".changelog" / "role-ic-sales" / "v1.2.0.md"
    assert archived.exists()
    # And it should NOT be under core/
    assert not (template / ".changelog" / "core" / "v1.2.0.md").exists()


def test_multi_axis_versions_map_populated(fake_repos, capsys):
    """TEMPLATE_VERSION.json grows a `versions: {scope: version}` map."""
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "core-thing.md").write_text("# Core\n")
    (jay / "Portfolio Brain" / "_skills" / "tech-thing.md").write_text("# Tech\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: core change
changes:
  - type: add_file
    path: Portfolio Brain/_skills/core-thing.md
    rationale: r
---
""")
    _write_changes_file(jay, "v1.2.0.md", """---
version: 1.2.0
date: 2026-05-14
type: minor
scope: role:ic-tech
summary: tech-only change
changes:
  - type: add_file
    path: Portfolio Brain/_skills/tech-thing.md
    rationale: r
---
""")
    _commit_all(jay, "both")

    assert sync.run(jay) == 0
    version_data = json.loads((template / "TEMPLATE_VERSION.json").read_text())
    assert version_data["versions"]["core"] == "1.1.0"
    assert version_data["versions"]["role:ic-tech"] == "1.2.0"


def test_dry_run_does_not_archive(fake_repos, capsys):
    """Dry-run skips the archive write just like it skips file mutations."""
    jay, template = fake_repos
    (jay / "Portfolio Brain" / "_skills" / "dry-arch.md").write_text("# Dry\n")
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
summary: dry
changes:
  - type: add_file
    path: Portfolio Brain/_skills/dry-arch.md
    rationale: r
---
""")
    _commit_all(jay, "dry archive")

    assert sync.run(jay, dry_run=True) == 0
    assert not (template / ".changelog").exists()


def test_invalid_scope_raises_validation_error(fake_repos):
    """Scope must be 'core' or 'role:<name>'. Anything else aborts."""
    jay, _ = fake_repos
    _write_changes_file(jay, "v1.1.0.md", """---
version: 1.1.0
date: 2026-05-14
type: minor
scope: bogus_scope
summary: bad
changes:
  - type: add_file
    path: Portfolio Brain/_skills/x.md
    rationale: r
---
""")
    _commit_all(jay, "bad scope")

    with pytest.raises(sync.ValidationError, match="invalid scope"):
        sync.run(jay)
