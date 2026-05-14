#!/usr/bin/env python3
"""Sync entropy-template/ from Jay's upstream repo by reading CHANGES/*.md.

Run from CI on a schedule. Reads .jay-sync-manifest.json, fetches Jay's repo,
finds new CHANGES/vX.Y.Z.md files since last_synced_commit, validates their
frontmatter, applies each handler entry to entropy-template/, updates the
manifest + TEMPLATE_VERSION.json, and prints a PR body to stdout.

Output:
- Modifies files under entropy-template/ in place (unless --dry-run)
- Prints a GitHub-Actions-friendly multi-line PR body to stdout. The first
  line is the PR title; the rest is the body. (Workflow file picks it up.)
- Exit code: 0 = ready for PR; 2 = nothing to do; 1 = error.

Usage:
    python scripts/sync_from_entropy.py [--jay-repo-path PATH] [--dry-run]

If --jay-repo-path is omitted, the script does `git clone` of jaykhalife/entropy
into a temp directory. (CI must have a token with read access.)
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = REPO_ROOT / "entropy-template"
MANIFEST_PATH = TEMPLATE_ROOT / ".jay-sync-manifest.json"
VERSION_FILE = TEMPLATE_ROOT / "TEMPLATE_VERSION.json"
CHANGES_DIR = "CHANGES"

VALID_HANDLERS = {"rename", "add_file", "delete_file", "structure_split", "content_patch"}
VALID_CLASSIFIERS = {
    "participant_domain_majority",
    "frontmatter_field_match",
    "filename_regex",
    "manual",
}
SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)\.md$")


# -----------------------------------------------------------------------------
# I/O helpers
# -----------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _stringify_dates(obj):
    """Recursively convert datetime.date / datetime instances to ISO strings.

    PyYAML parses unquoted YYYY-MM-DD as datetime.date, which json.dumps can't
    serialize. We normalize before writing anything derived from frontmatter.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()[:10] if isinstance(obj, date) and not isinstance(obj, datetime) else obj.isoformat()
    if isinstance(obj, dict):
        return {k: _stringify_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_dates(v) for v in obj]
    return obj


def _read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def _write_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


def _read_version_file() -> dict:
    if VERSION_FILE.exists():
        return json.loads(VERSION_FILE.read_text())
    return {"version": "0.0.0", "updated": date.today().isoformat(), "history": []}


def _write_version_file(data: dict) -> None:
    VERSION_FILE.write_text(json.dumps(data, indent=2) + "\n")


# -----------------------------------------------------------------------------
# Jay repo access
# -----------------------------------------------------------------------------

def _clone_jay_repo(repo: str, branch: str, dest: Path) -> None:
    subprocess.run(
        ["git", "clone", "--depth", "50", "--branch", branch, f"https://github.com/{repo}.git", str(dest)],
        check=True, capture_output=True, text=True,
    )


def _jay_head_sha(jay_repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(jay_repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


# -----------------------------------------------------------------------------
# CHANGES file parsing + validation
# -----------------------------------------------------------------------------

class ValidationError(Exception):
    pass


def _list_change_files(jay_repo: Path) -> list[Path]:
    changes_dir = jay_repo / CHANGES_DIR
    if not changes_dir.is_dir():
        return []
    return sorted([p for p in changes_dir.glob("v*.md") if SEMVER_RE.match(p.name)])


def _parse_change_file(path: Path) -> dict:
    raw = path.read_text()
    if not raw.startswith("---"):
        raise ValidationError(f"{path.name}: missing YAML frontmatter")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValidationError(f"{path.name}: malformed frontmatter (no closing ---)")
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise ValidationError(f"{path.name}: YAML parse error: {e}") from None
    if not isinstance(meta, dict):
        raise ValidationError(f"{path.name}: frontmatter is not a mapping")
    meta = _stringify_dates(meta)
    prose = parts[2].strip()
    return {"meta": meta, "prose": prose, "filename": path.name}


def _validate_change_entry(filename: str, entry: dict, idx: int) -> None:
    """Raise ValidationError if a single `changes[i]` entry is malformed."""
    prefix = f"{filename} changes[{idx}]"
    if not isinstance(entry, dict):
        raise ValidationError(f"{prefix}: not a mapping")
    handler = entry.get("type")
    if handler not in VALID_HANDLERS:
        raise ValidationError(f"{prefix}: unknown handler type {handler!r}")
    if not entry.get("rationale"):
        raise ValidationError(f"{prefix}: missing rationale")

    if handler == "rename":
        for field in ("from", "to"):
            if not entry.get(field):
                raise ValidationError(f"{prefix} ({handler}): missing field {field!r}")
    elif handler in ("add_file", "delete_file", "content_patch"):
        if not entry.get("path"):
            raise ValidationError(f"{prefix} ({handler}): missing field 'path'")
    elif handler == "structure_split":
        if not entry.get("from"):
            raise ValidationError(f"{prefix} ({handler}): missing field 'from'")
        dests = entry.get("to")
        if not isinstance(dests, list) or len(dests) < 2:
            raise ValidationError(f"{prefix} ({handler}): 'to' must be a list of at least 2 paths")
        classifier = entry.get("classifier")
        if not isinstance(classifier, dict):
            raise ValidationError(f"{prefix} ({handler}): missing classifier mapping")
        if classifier.get("method") not in VALID_CLASSIFIERS:
            raise ValidationError(
                f"{prefix} ({handler}): unknown classifier method {classifier.get('method')!r}"
            )


def _validate_change_file(parsed: dict) -> None:
    meta = parsed["meta"]
    filename = parsed["filename"]
    file_version = SEMVER_RE.match(filename).group(0)[1:-3]  # strip leading 'v' and '.md'
    declared_version = meta.get("version")
    if declared_version != file_version:
        raise ValidationError(
            f"{filename}: frontmatter version {declared_version!r} does not match filename version {file_version!r}"
        )
    if meta.get("type") not in {"major", "minor", "patch"}:
        raise ValidationError(f"{filename}: 'type' must be one of major/minor/patch")
    changes = meta.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ValidationError(f"{filename}: 'changes' must be a non-empty list")
    for i, entry in enumerate(changes):
        _validate_change_entry(filename, entry, i)


# -----------------------------------------------------------------------------
# Handler application
# -----------------------------------------------------------------------------

def _path_is_tracked(path: str, tracked_paths: list[str]) -> bool:
    for tp in tracked_paths:
        if tp.endswith("/") and path.startswith(tp):
            return True
        if path == tp:
            return True
    return False


def _apply_rename(entry: dict, manifest: dict, dry_run: bool) -> list[str]:
    src_rel = entry["from"].rstrip("/")
    dst_rel = entry["to"].rstrip("/")
    src_abs = TEMPLATE_ROOT / src_rel
    dst_abs = TEMPLATE_ROOT / dst_rel
    if not src_abs.exists():
        raise ValidationError(f"rename: source {src_rel!r} does not exist in template")
    if dst_abs.exists():
        raise ValidationError(f"rename: destination {dst_rel!r} already exists in template")
    if not dry_run:
        dst_abs.parent.mkdir(parents=True, exist_ok=True)
        src_abs.rename(dst_abs)
    # Update manifest file entries (in-memory; final write is gated by dry_run upstream)
    affected = []
    rewritten: dict[str, dict] = {}
    for path, info in manifest["files"].items():
        if path == src_rel or path.startswith(src_rel + "/"):
            new_path = dst_rel + path[len(src_rel):]
            info["dest_path_in_template"] = f"entropy-template/{new_path}"
            rewritten[new_path] = info
            affected.append(f"{path} -> {new_path}")
        else:
            rewritten[path] = info
    manifest["files"] = rewritten
    return affected


def _apply_add_file(entry: dict, jay_repo: Path, manifest: dict, version: str, dry_run: bool) -> list[str]:
    rel = entry["path"]
    if not _path_is_tracked(rel, manifest["tracked_paths"]):
        raise ValidationError(f"add_file: {rel!r} is outside tracked_paths; widen tracked_paths or fix the entry")
    src = jay_repo / rel
    if not src.is_file():
        raise ValidationError(f"add_file: {rel!r} does not exist in Jay's repo at this commit")
    dst = TEMPLATE_ROOT / rel
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    manifest["files"][rel] = {
        "source_sha256": _sha256(src),  # hash from Jay's side — safe in dry-run too
        "dest_path_in_template": f"entropy-template/{rel}",
        "first_seen_version": version,
        "last_updated_version": version,
    }
    return [f"added {rel}"]


def _apply_delete_file(entry: dict, manifest: dict, dry_run: bool) -> list[str]:
    rel = entry["path"]
    if rel not in manifest["files"]:
        raise ValidationError(f"delete_file: {rel!r} not in manifest")
    target = TEMPLATE_ROOT / rel
    if not dry_run and target.exists():
        target.unlink()
    del manifest["files"][rel]
    return [f"deleted {rel}"]


def _apply_content_patch(entry: dict, jay_repo: Path, manifest: dict, version: str, dry_run: bool) -> list[str]:
    rel = entry["path"]
    if rel not in manifest["files"]:
        raise ValidationError(f"content_patch: {rel!r} not in manifest; add_file first")
    src = jay_repo / rel
    if not src.is_file():
        raise ValidationError(f"content_patch: {rel!r} missing in Jay's repo at this commit")
    dst = TEMPLATE_ROOT / rel
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    manifest["files"][rel]["source_sha256"] = _sha256(src)
    manifest["files"][rel]["last_updated_version"] = version
    return [f"patched {rel}"]


def _apply_structure_split(entry: dict, manifest: dict) -> list[str]:
    """Bot-side: just create the destination folders + flag for human review.

    The actual per-file classification happens in the migration applier
    (runs against user vaults). For the entropy-template/ side, the bot leaves
    files in place — entropy-template/ is a template, not user data, so there's
    nothing to classify yet. The entry is recorded so user-side applier can
    replay it later.
    """
    src_rel = entry["from"].rstrip("/")
    src_abs = TEMPLATE_ROOT / src_rel
    affected = [f"structure_split: {src_rel} -> {entry['to']} (recorded; applies to user vaults only)"]
    # If src doesn't exist in template, that's fine — it might be a user-only
    # folder Jay introduced via convention. Just record the migration.
    if src_abs.is_dir():
        affected.append(f"  ({src_rel} exists in template — no per-file moves needed at template level)")
    return affected


def _apply_change_entry(entry: dict, jay_repo: Path, manifest: dict, version: str, dry_run: bool) -> list[str]:
    handler = entry["type"]
    if handler == "rename":
        return _apply_rename(entry, manifest, dry_run)
    if handler == "add_file":
        return _apply_add_file(entry, jay_repo, manifest, version, dry_run)
    if handler == "delete_file":
        return _apply_delete_file(entry, manifest, dry_run)
    if handler == "content_patch":
        return _apply_content_patch(entry, jay_repo, manifest, version, dry_run)
    if handler == "structure_split":
        return _apply_structure_split(entry, manifest)
    raise ValidationError(f"unknown handler {handler!r}")  # belt-and-suspenders


# -----------------------------------------------------------------------------
# Drift detection
# -----------------------------------------------------------------------------

def _detect_drift(jay_repo: Path, manifest: dict, processed_paths: set[str]) -> list[str]:
    """List files where Jay's hash differs from manifest, that no CHANGES entry covered."""
    drift = []
    for rel, info in manifest["files"].items():
        if rel in processed_paths:
            continue  # change was covered by a CHANGES entry
        jay_path = jay_repo / rel
        if not jay_path.is_file():
            drift.append(f"missing in Jay's repo: {rel}")
            continue
        if _sha256(jay_path) != info["source_sha256"]:
            drift.append(f"content changed without CHANGES entry: {rel}")
    return drift


# -----------------------------------------------------------------------------
# Main flow
# -----------------------------------------------------------------------------

def _processed_paths_for(entries: list[dict]) -> set[str]:
    """Return the set of paths touched by a list of validated change entries."""
    out: set[str] = set()
    for e in entries:
        if e["type"] in ("add_file", "delete_file", "content_patch"):
            out.add(e["path"])
        elif e["type"] == "rename":
            out.add(e["from"].rstrip("/"))
        elif e["type"] == "structure_split":
            out.add(e["from"].rstrip("/"))
    return out


def run(jay_repo: Path, dry_run: bool = False) -> int:
    manifest = _read_manifest()
    version_data = _read_version_file()

    jay_head = _jay_head_sha(jay_repo)
    if jay_head == manifest["last_synced_commit"]:
        print(f"SYNC: nothing to do (Jay HEAD == last_synced_commit == {jay_head[:7]})", file=sys.stderr)
        return 2

    # Discover new CHANGES files
    all_changes = _list_change_files(jay_repo)
    ingested_versions = {c["version"] for c in manifest["ingested_changes"]}
    new_changes = []
    for cf in all_changes:
        parsed = _parse_change_file(cf)
        if parsed["meta"]["version"] in ingested_versions:
            continue
        _validate_change_file(parsed)
        new_changes.append(parsed)

    if not new_changes:
        # No new CHANGES — still check for drift
        drift = _detect_drift(jay_repo, manifest, set())
        if not drift:
            print(f"SYNC: nothing to do (no new CHANGES, no drift)", file=sys.stderr)
            return 2
        # Drift but no CHANGES — still want a PR so reviewer sees it
        title = "sync: drift detected in Jay's repo (no CHANGES entry)"
        body = _build_pr_body([], drift, jay_head, manifest)
        if not dry_run:
            manifest["last_synced_commit"] = jay_head
            manifest["last_synced_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _write_manifest(manifest)
        _emit_pr(title, body)
        return 0

    # Apply changes in version order
    new_changes.sort(key=lambda p: tuple(int(x) for x in p["meta"]["version"].split(".")))
    summaries: list[dict] = []
    all_processed_paths: set[str] = set()

    for parsed in new_changes:
        meta = parsed["meta"]
        version = meta["version"]
        entry_summaries = []
        for entry in meta["changes"]:
            actions = _apply_change_entry(entry, jay_repo, manifest, version, dry_run)
            entry_summaries.append({"type": entry["type"], "actions": actions, "entry": entry})
        all_processed_paths |= _processed_paths_for(meta["changes"])
        summaries.append({"version": version, "meta": meta, "prose": parsed["prose"], "entries": entry_summaries})

        # Append to TEMPLATE_VERSION.json
        version_data["version"] = version
        version_data["updated"] = meta.get("date") or date.today().isoformat()
        version_data.setdefault("history", []).insert(0, {
            "version": version,
            "date": meta.get("date") or date.today().isoformat(),
            "summary": meta.get("summary", ""),
            "changes": [
                {k: v for k, v in entry.items() if k != "rationale"} | {"description": entry.get("rationale", "")}
                for entry in meta["changes"]
            ],
        })

        manifest["ingested_changes"].append({
            "version": version,
            "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_commit": jay_head,
        })

    drift = _detect_drift(jay_repo, manifest, all_processed_paths)

    if not dry_run:
        manifest["last_synced_commit"] = jay_head
        manifest["last_synced_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write_manifest(manifest)
        _write_version_file(version_data)

    versions_list = ", ".join(s["version"] for s in summaries)
    title = f"sync: Jay v{summaries[-1]['version']} ({versions_list})"
    body = _build_pr_body(summaries, drift, jay_head, manifest)
    _emit_pr(title, body)
    return 0


def _build_pr_body(summaries: list[dict], drift: list[str], jay_head: str, manifest: dict) -> str:
    lines = [
        f"Synced from `{manifest['source_repo']}@{jay_head[:7]}`.",
        "",
    ]
    if summaries:
        lines.append("## New versions")
        for s in summaries:
            lines.append(f"### v{s['version']} — {s['meta'].get('summary', '')}")
            for entry_sum in s["entries"]:
                entry = entry_sum["entry"]
                lines.append(f"- **{entry['type']}**: {entry.get('rationale', '')}")
                for action in entry_sum["actions"]:
                    lines.append(f"  - `{action}`")
            if s["prose"]:
                lines.append("")
                lines.append("<details><summary>Full notes from Jay</summary>")
                lines.append("")
                lines.append(s["prose"])
                lines.append("")
                lines.append("</details>")
            lines.append("")
    if drift:
        lines.append("## Drift detected (no CHANGES entry covers these)")
        for d in drift:
            lines.append(f"- {d}")
        lines.append("")
        lines.append("Ask Jay to write a CHANGES/vX.Y.Z.md describing these, or merge as-is.")
    return "\n".join(lines)


def _emit_pr(title: str, body: str) -> None:
    """Print PR title (first line) + body so the GH Action can capture it."""
    print(title)
    print(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jay-repo-path", help="Path to a local clone of Jay's repo (otherwise: clone fresh)")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify any files; only print proposed PR")
    args = parser.parse_args()

    if args.jay_repo_path:
        return run(Path(args.jay_repo_path).resolve(), dry_run=args.dry_run)

    manifest = _read_manifest()
    with tempfile.TemporaryDirectory() as tmp:
        jay_clone = Path(tmp) / "jay"
        _clone_jay_repo(manifest["source_repo"], manifest["source_branch"], jay_clone)
        return run(jay_clone, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
