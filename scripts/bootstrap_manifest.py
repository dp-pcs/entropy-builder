#!/usr/bin/env python3
"""Populate entropy-template/.jay-sync-manifest.json from current contents.

Run this ONCE to initialize the manifest before the sync bot's first run.
After bootstrap, the bot only sees changes after `last_synced_commit`, so
no flood of false drift.

Usage:
    python scripts/bootstrap_manifest.py [--jay-repo-head <sha>]

If --jay-repo-head is omitted, the script calls `gh api` to read the current
HEAD of jaykhalife/entropy main.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = REPO_ROOT / "entropy-template"
MANIFEST_PATH = TEMPLATE_ROOT / ".jay-sync-manifest.json"

DEFAULT_TRACKED_PATHS = [
    "Portfolio Brain/_skills/",
    "Portfolio Brain/_analytics/",
    "Portfolio Brain/Company-Rules.md",
]

DEFAULT_SOURCE_REPO = "jaykhalife/entropy"
DEFAULT_SOURCE_BRANCH = "main"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _resolve_jay_head() -> str:
    """Call gh CLI to get the current main HEAD of Jay's repo."""
    result = subprocess.run(
        ["gh", "api", f"repos/{DEFAULT_SOURCE_REPO}/commits/{DEFAULT_SOURCE_BRANCH}", "--jq", ".sha"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _iter_tracked_files(template_root: Path, tracked_paths: list[str]):
    """Yield (vault_relative_path, absolute_path) for every file matched by tracked_paths."""
    for entry in tracked_paths:
        target = template_root / entry
        if entry.endswith("/"):
            if not target.is_dir():
                continue
            for f in sorted(target.rglob("*")):
                if f.is_file():
                    yield str(f.relative_to(template_root)).replace("\\", "/"), f
        else:
            if target.is_file():
                yield entry, target


def build_manifest(jay_head: str, tracked_paths: list[str]) -> dict:
    files: dict[str, dict] = {}
    for rel_path, abs_path in _iter_tracked_files(TEMPLATE_ROOT, tracked_paths):
        files[rel_path] = {
            "source_sha256": _sha256(abs_path),
            "dest_path_in_template": f"entropy-template/{rel_path}",
            "first_seen_version": "bootstrap",
            "last_updated_version": "bootstrap",
        }
    return {
        "schema_version": 1,
        "source_repo": DEFAULT_SOURCE_REPO,
        "source_branch": DEFAULT_SOURCE_BRANCH,
        "last_synced_commit": jay_head,
        "last_synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tracked_paths": tracked_paths,
        "files": files,
        "ingested_changes": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jay-repo-head", help="Override Jay's repo HEAD SHA (default: resolve via gh)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing manifest")
    args = parser.parse_args()

    if MANIFEST_PATH.exists() and not args.force:
        print(f"refusing to overwrite existing manifest at {MANIFEST_PATH} (use --force)", file=sys.stderr)
        sys.exit(2)

    jay_head = args.jay_repo_head or _resolve_jay_head()
    if not jay_head or len(jay_head) < 7:
        print(f"invalid Jay-repo HEAD: {jay_head!r}", file=sys.stderr)
        sys.exit(1)

    manifest = build_manifest(jay_head, DEFAULT_TRACKED_PATHS)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {MANIFEST_PATH}")
    print(f"  tracking {len(manifest['files'])} files")
    print(f"  pinned to Jay-repo commit {jay_head[:7]}")


if __name__ == "__main__":
    main()
