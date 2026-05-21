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
import json
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Make pipeline.migrations importable when running as a script from anywhere.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.migrations import handlers, parser, paths  # noqa: E402
from pipeline.migrations.schema import ValidationError  # noqa: E402, F401 — re-exported for test compat

TEMPLATE_ROOT = REPO_ROOT / "entropy-template"
MANIFEST_PATH = TEMPLATE_ROOT / ".jay-sync-manifest.json"
VERSION_FILE = TEMPLATE_ROOT / "TEMPLATE_VERSION.json"


# -----------------------------------------------------------------------------
# I/O helpers (template-side state files)
# -----------------------------------------------------------------------------

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
# Drift detection
# -----------------------------------------------------------------------------

def _detect_drift(jay_repo: Path, manifest: dict, processed_paths: set[str]) -> list[str]:
    """List files where Jay's hash differs from manifest, that no CHANGES entry covered.

    Tracked-but-excluded files are not in manifest['files'] in the first place, so
    they're naturally absent here. We also walk Jay's tracked_paths to catch any
    new files Jay added in tracked dirs that aren't yet in the manifest (would
    indicate a missing add_file CHANGES entry).
    """
    excluded = manifest.get("excluded_paths", [])
    drift = []
    for rel, info in manifest["files"].items():
        if rel in processed_paths:
            continue
        jay_path = jay_repo / rel
        if not jay_path.is_file():
            drift.append(f"missing in Jay's repo: {rel}")
            continue
        if paths.sha256_of_path(jay_path) != info["source_sha256"]:
            drift.append(f"content changed without CHANGES entry: {rel}")
    for tp in manifest["tracked_paths"]:
        target = jay_repo / tp
        if tp.endswith("/") and target.is_dir():
            for f in sorted(target.rglob("*")):
                if not f.is_file():
                    continue
                rel = str(f.relative_to(jay_repo)).replace("\\", "/")
                if rel in manifest["files"] or rel in processed_paths:
                    continue
                if paths.path_is_excluded(rel, excluded):
                    continue
                drift.append(f"new file in tracked path without CHANGES entry: {rel}")
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
    all_changes = parser.list_change_files(jay_repo)
    ingested_versions = {c["version"] for c in manifest["ingested_changes"]}
    new_changes = []
    for cf in all_changes:
        parsed = parser.parse_change_file(cf)
        if parsed["meta"]["version"] in ingested_versions:
            continue
        parser.validate_change_file(parsed)
        parsed["__source_path"] = cf  # carry for archival into entropy-template/.changelog/
        new_changes.append(parsed)

    if not new_changes:
        drift = _detect_drift(jay_repo, manifest, set())
        if not drift:
            print("SYNC: nothing to do (no new CHANGES, no drift)", file=sys.stderr)
            return 2
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
        scope = meta.get("scope", "core")
        entry_summaries = []
        for entry in meta["changes"]:
            actions = handlers.apply_change_entry(
                entry, jay_repo, manifest, version, dry_run, target_root=TEMPLATE_ROOT,
            )
            entry_summaries.append({"type": entry["type"], "actions": actions, "entry": entry})
        all_processed_paths |= _processed_paths_for(meta["changes"])
        summaries.append({"version": version, "meta": meta, "prose": parsed["prose"], "entries": entry_summaries})

        # Archive the original CHANGES file so the /api/migrations endpoint can serve it.
        # Bucketed by scope (role: colon → dash for filesystem-friendliness).
        if not dry_run:
            scope_dir_name = scope.replace(":", "-")
            archive_dir = TEMPLATE_ROOT / ".changelog" / scope_dir_name
            archive_dir.mkdir(parents=True, exist_ok=True)
            src_path = parsed["__source_path"]
            (archive_dir / src_path.name).write_bytes(src_path.read_bytes())

        version_data["version"] = version  # legacy: latest applied version (any scope)
        version_data["updated"] = meta.get("date") or date.today().isoformat()
        version_data.setdefault("versions", {})[scope] = version  # multi-axis (see [[entropy-versioning]])
        version_data.setdefault("history", []).insert(0, {
            "version": version,
            "date": meta.get("date") or date.today().isoformat(),
            "summary": meta.get("summary", ""),
            "scope": scope,
            "changes": [
                {k: v for k, v in entry.items() if k != "rationale"} | {"description": entry.get("rationale", "")}
                for entry in meta["changes"]
            ],
        })

        manifest["ingested_changes"].append({
            "version": version,
            "scope": scope,
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
            scope = s["meta"].get("scope", "core")
            scope_tag = "" if scope == "core" else f" *(scope: {scope})*"
            lines.append(f"### v{s['version']} — {s['meta'].get('summary', '')}{scope_tag}")
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
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument("--jay-repo-path", help="Path to a local clone of Jay's repo (otherwise: clone fresh)")
    arg_parser.add_argument("--dry-run", action="store_true", help="Do not modify any files; only print proposed PR")
    args = arg_parser.parse_args()

    if args.jay_repo_path:
        return run(Path(args.jay_repo_path).resolve(), dry_run=args.dry_run)

    manifest = _read_manifest()
    with tempfile.TemporaryDirectory() as tmp:
        jay_clone = Path(tmp) / "jay"
        _clone_jay_repo(manifest["source_repo"], manifest["source_branch"], jay_clone)
        return run(jay_clone, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
