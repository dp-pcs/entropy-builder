"""Migration applier — replays version-ordered CHANGES against a user's vault.

Counterpart to scripts/sync_from_entropy.py: where the bot mutates the
*template*, this mutates the *vault*. Both call into the same parser/handlers
core so semantics cannot drift between sides.

Conflict principle (non-negotiable): never silently overwrite a user edit.
Diverged files are preserved; `content_patch` drops a `<path>.new` sidecar.

Divergence detection: if `<vault>/.vault-manifest.json` exists, use its
`source_sha256` per file as the last-known hash for precise comparison. If
absent, fall back to **conservative-preserve** — any content difference is
treated as a potential edit and preserved. See bd-ez3 follow-up for the
builder-side manifest emission that turns this into precise tracking.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from . import classifiers, client, parser, report
from .paths import path_is_excluded, sha256_of_path
from .schema import SCOPE_CORE, SEMVER_RE, ValidationError


# -----------------------------------------------------------------------------
# Vault state helpers
# -----------------------------------------------------------------------------

VAULT_VERSION_FILE = "vault_version.json"
VAULT_MANIFEST_FILE = ".vault-manifest.json"


def read_vault_version(vault_root: Path) -> Optional[str]:
    """Return the template_version recorded in `vault_version.json`, or None."""
    path = vault_root / VAULT_VERSION_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    return data.get("template_version")


def bump_vault_version(vault_root: Path, new_version: str) -> None:
    path = vault_root / VAULT_VERSION_FILE
    if path.is_file():
        data = json.loads(path.read_text())
    else:
        data = {}
    data["template_version"] = new_version
    data.setdefault("update_check_url", "https://entropy.elelem.expert/api/template/version")
    path.write_text(json.dumps(data, indent=2) + "\n")


def read_vault_manifest(vault_root: Path) -> Optional[dict]:
    path = vault_root / VAULT_MANIFEST_FILE
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def write_vault_manifest(vault_root: Path, manifest: dict) -> None:
    (vault_root / VAULT_MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n")


# -----------------------------------------------------------------------------
# Semver helpers
# -----------------------------------------------------------------------------

def _parse_semver(v: str) -> tuple[int, int, int]:
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValidationError(f"not a semver: {v!r}")
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


def _semver_gt(a: str, b: str) -> bool:
    return _parse_semver(a) > _parse_semver(b)


def list_local_versions(local_source: Path, scope: str = SCOPE_CORE) -> list[str]:
    """Scan `<local_source>/.changelog/<scope_dir>/v*.md` for available versions."""
    scope_dir = scope.replace(":", "-")
    base = local_source / ".changelog" / scope_dir
    if not base.is_dir():
        return []
    versions: list[str] = []
    for p in base.glob("v*.md"):
        m = SEMVER_RE.match(p.name)
        if m:
            versions.append(p.name[1:-3])  # strip leading 'v' and trailing '.md'
    versions.sort(key=_parse_semver)
    return versions


# -----------------------------------------------------------------------------
# Wikilink rewriter (rename handler)
# -----------------------------------------------------------------------------

_WIKILINK_RE = re.compile(r"\[\[([^\]\|]+)(\|[^\]]+)?\]\]")


def _rewrite_wikilinks_in_text(text: str, from_path: str, to_path: str) -> tuple[str, int]:
    """Rewrite `[[from_path/...]]` and `[[from_path]]` to point at `to_path`.

    Matches the exact path or a prefix-with-slash. Preserves alias (`|label`).
    Returns (new_text, count).
    """
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        target = m.group(1)
        alias = m.group(2) or ""
        if target == from_path:
            new_target = to_path
        elif target.startswith(from_path + "/"):
            new_target = to_path + target[len(from_path):]
        else:
            return m.group(0)
        count += 1
        return f"[[{new_target}{alias}]]"

    new_text = _WIKILINK_RE.sub(sub, text)
    return new_text, count


def _rewrite_wikilinks_in_vault(vault_root: Path, from_path: str, to_path: str, dry_run: bool) -> int:
    """Rewrite all `[[from_path...]]` wikilinks under vault_root. Returns count."""
    # Strip extension from path → wikilinks reference files by stem-ish path.
    # Jay's convention: `[[Portfolio Brain/Customers/Acme]]` (no .md). We try
    # both with and without `.md` since some links carry the extension.
    candidates = [from_path, _strip_md(from_path)]
    targets = [to_path, _strip_md(to_path)]
    total = 0
    for md in vault_root.rglob("*.md"):
        text = md.read_text()
        for src, dst in zip(candidates, targets):
            text, n = _rewrite_wikilinks_in_text(text, src, dst)
            total += n
        if not dry_run:
            md.write_text(text)
    return total


def _strip_md(p: str) -> str:
    return p[:-3] if p.endswith(".md") else p


# -----------------------------------------------------------------------------
# Vault-side handlers (conflict-aware)
# -----------------------------------------------------------------------------

@dataclass
class ApplyContext:
    vault_root: Path
    source_root: Path
    manifest: Optional[dict]   # vault-side .vault-manifest.json (may be None)
    excluded_paths: list[str]
    dry_run: bool


def _excluded(ctx: ApplyContext, rel: str) -> bool:
    return path_is_excluded(rel, ctx.excluded_paths)


def _known_hash(ctx: ApplyContext, rel: str) -> Optional[str]:
    if not ctx.manifest:
        return None
    entry = ctx.manifest.get("files", {}).get(rel)
    return entry.get("source_sha256") if entry else None


def _record_hash(ctx: ApplyContext, rel: str, src: Path, version: str) -> None:
    if ctx.manifest is None or ctx.dry_run:
        return
    files = ctx.manifest.setdefault("files", {})
    files[rel] = {
        "source_sha256": sha256_of_path(src),
        "last_updated_version": version,
    }


def _drop_hash(ctx: ApplyContext, rel: str) -> None:
    if ctx.manifest is None or ctx.dry_run:
        return
    ctx.manifest.get("files", {}).pop(rel, None)


def apply_add_file_vault(entry: dict, ctx: ApplyContext, version: str) -> report.EntryResult:
    rel = entry["path"]
    r = report.EntryResult(version=version, handler="add_file", summary=f"add {rel}", status="applied")
    if _excluded(ctx, rel):
        r.status = "skipped"
        r.summary = f"skipped (excluded): {rel}"
        return r
    src = ctx.source_root / rel
    if not src.is_file():
        r.status = "skipped"
        r.summary = f"source missing in payload: {rel}"
        return r
    dst = ctx.vault_root / rel
    if dst.exists():
        if dst.is_file() and sha256_of_path(dst) == sha256_of_path(src):
            r.status = "noop"
            r.summary = f"already present: {rel}"
            return r
        # Conflict — preserve local, write .new sidecar.
        sidecar = dst.with_name(dst.name + ".new")
        if not ctx.dry_run:
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, sidecar)
        r.status = "conflict"
        r.summary = f"add_file collision: kept local, wrote {sidecar.relative_to(ctx.vault_root)}"
        r.conflict_paths.append(str(dst.relative_to(ctx.vault_root)))
        return r
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    _record_hash(ctx, rel, src, version)
    r.summary = f"added {rel}"
    return r


def apply_delete_file_vault(entry: dict, ctx: ApplyContext, version: str) -> report.EntryResult:
    rel = entry["path"]
    r = report.EntryResult(version=version, handler="delete_file", summary=f"delete {rel}", status="applied")
    if _excluded(ctx, rel):
        r.status = "skipped"
        r.summary = f"skipped (excluded): {rel}"
        return r
    dst = ctx.vault_root / rel
    if not dst.exists():
        r.status = "noop"
        r.summary = f"already absent: {rel}"
        _drop_hash(ctx, rel)
        return r
    if not dst.is_file():
        r.status = "skipped"
        r.summary = f"refusing to delete non-file: {rel}"
        return r
    known = _known_hash(ctx, rel)
    local = sha256_of_path(dst)
    safe_to_delete = known is not None and known == local
    if not safe_to_delete:
        # Conservative-preserve: keep local copy, report.
        r.status = "conflict"
        r.summary = (
            f"delete skipped — local diverged or no prior hash: kept {rel}"
        )
        r.conflict_paths.append(rel)
        return r
    if not ctx.dry_run:
        dst.unlink()
    _drop_hash(ctx, rel)
    r.summary = f"deleted {rel}"
    return r


def apply_content_patch_vault(entry: dict, ctx: ApplyContext, version: str) -> report.EntryResult:
    rel = entry["path"]
    r = report.EntryResult(version=version, handler="content_patch", summary=f"patch {rel}", status="applied")
    if _excluded(ctx, rel):
        r.status = "skipped"
        r.summary = f"skipped (excluded): {rel}"
        return r
    src = ctx.source_root / rel
    if not src.is_file():
        r.status = "skipped"
        r.summary = f"source missing in payload: {rel}"
        return r
    dst = ctx.vault_root / rel
    new_hash = sha256_of_path(src)

    if not dst.exists():
        # User deleted it locally; treat as conflict and drop a .new for review.
        sidecar = dst.with_name(dst.name + ".new")
        if not ctx.dry_run:
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, sidecar)
        r.status = "conflict"
        r.summary = f"patch on locally-deleted file: wrote {sidecar.relative_to(ctx.vault_root)}"
        r.conflict_paths.append(rel)
        return r

    local_hash = sha256_of_path(dst)
    if local_hash == new_hash:
        r.status = "noop"
        r.summary = f"already current: {rel}"
        _record_hash(ctx, rel, src, version)
        return r

    known = _known_hash(ctx, rel)
    clean_overwrite = known is not None and known == local_hash
    if clean_overwrite:
        if not ctx.dry_run:
            shutil.copyfile(src, dst)
        _record_hash(ctx, rel, src, version)
        r.summary = f"patched {rel}"
        return r

    # Diverged (or no prior hash to compare): preserve local, write .new.
    sidecar = dst.with_name(dst.name + ".new")
    if not ctx.dry_run:
        shutil.copyfile(src, sidecar)
    r.status = "conflict"
    r.summary = (
        f"local edits detected: kept {rel}, wrote {sidecar.relative_to(ctx.vault_root)}"
    )
    r.conflict_paths.append(rel)
    return r


def apply_rename_vault(entry: dict, ctx: ApplyContext, version: str) -> report.EntryResult:
    src_rel = entry["from"].rstrip("/")
    dst_rel = entry["to"].rstrip("/")
    r = report.EntryResult(
        version=version, handler="rename", summary=f"rename {src_rel} -> {dst_rel}", status="applied",
    )
    if _excluded(ctx, src_rel) and _excluded(ctx, dst_rel):
        r.status = "skipped"
        r.summary = f"skipped (excluded): rename {src_rel} -> {dst_rel}"
        return r
    src_abs = ctx.vault_root / src_rel
    dst_abs = ctx.vault_root / dst_rel
    if dst_abs.exists() and not src_abs.exists():
        r.status = "noop"
        r.summary = f"already renamed: {dst_rel} exists"
        return r
    if src_abs.exists() and dst_abs.exists():
        r.status = "conflict"
        r.summary = f"both {src_rel} and {dst_rel} exist; left untouched"
        r.conflict_paths.extend([src_rel, dst_rel])
        return r
    if not src_abs.exists() and not dst_abs.exists():
        r.status = "skipped"
        r.summary = f"neither {src_rel} nor {dst_rel} present in vault"
        return r
    # src exists, dst does not → move + rewrite wikilinks
    if not ctx.dry_run:
        dst_abs.parent.mkdir(parents=True, exist_ok=True)
        src_abs.rename(dst_abs)
    # Update vault manifest entries
    if ctx.manifest:
        files = ctx.manifest.get("files", {})
        rewritten: dict[str, dict] = {}
        for path, info in files.items():
            if path == src_rel or path.startswith(src_rel + "/"):
                new_path = dst_rel + path[len(src_rel):]
                rewritten[new_path] = info
            else:
                rewritten[path] = info
        ctx.manifest["files"] = rewritten
    r.links_rewritten = _rewrite_wikilinks_in_vault(ctx.vault_root, src_rel, dst_rel, ctx.dry_run)
    return r


def apply_structure_split_vault(entry: dict, ctx: ApplyContext, version: str) -> list[report.EntryResult]:
    src_rel = entry["from"].rstrip("/")
    destinations = [d.rstrip("/") + "/" for d in entry["to"]]
    classifier = entry["classifier"]
    results: list[report.EntryResult] = []
    src_abs = ctx.vault_root / src_rel
    if _excluded(ctx, src_rel):
        results.append(report.EntryResult(
            version=version, handler="structure_split", status="skipped",
            summary=f"skipped (excluded): structure_split from {src_rel}",
        ))
        return results
    if not src_abs.is_dir():
        results.append(report.EntryResult(
            version=version, handler="structure_split", status="skipped",
            summary=f"source folder missing: {src_rel}",
        ))
        return results

    for file_path in classifiers.iter_files(src_abs):
        rel_within = file_path.relative_to(src_abs).as_posix()
        try:
            dest_dir = classifiers.classify(file_path, classifier, destinations)
        except ValidationError as e:
            results.append(report.EntryResult(
                version=version, handler="structure_split", status="conflict",
                summary=f"classifier error on {rel_within}: {e}",
                conflict_paths=[f"{src_rel}/{rel_within}"],
            ))
            continue
        if dest_dir is None:
            # Manual: leave in place, flag for review.
            results.append(report.EntryResult(
                version=version, handler="structure_split", status="conflict",
                summary=f"manual classification required: {rel_within}",
                conflict_paths=[f"{src_rel}/{rel_within}"],
            ))
            continue
        dest_path = ctx.vault_root / dest_dir.rstrip("/") / rel_within
        if dest_path.exists():
            results.append(report.EntryResult(
                version=version, handler="structure_split", status="conflict",
                summary=f"split target exists: kept original at {src_rel}/{rel_within}",
                conflict_paths=[f"{src_rel}/{rel_within}", str(dest_path.relative_to(ctx.vault_root))],
            ))
            continue
        if not ctx.dry_run:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.rename(dest_path)
        results.append(report.EntryResult(
            version=version, handler="structure_split", status="applied",
            summary=f"moved {src_rel}/{rel_within} -> {dest_dir}{rel_within}",
        ))
    # If the source dir is now empty (and not dry-run), remove it.
    if not ctx.dry_run and src_abs.is_dir() and not any(src_abs.iterdir()):
        src_abs.rmdir()
    return results


_HANDLER_DISPATCH = {
    "add_file": apply_add_file_vault,
    "delete_file": apply_delete_file_vault,
    "content_patch": apply_content_patch_vault,
    "rename": apply_rename_vault,
}


def _apply_entry(entry: dict, ctx: ApplyContext, version: str) -> list[report.EntryResult]:
    handler = entry["type"]
    if handler == "structure_split":
        return apply_structure_split_vault(entry, ctx, version)
    fn = _HANDLER_DISPATCH.get(handler)
    if fn is None:
        raise ValidationError(f"unknown handler {handler!r}")
    return [fn(entry, ctx, version)]


# -----------------------------------------------------------------------------
# Orchestration
# -----------------------------------------------------------------------------

def apply(
    vault_root: Path,
    *,
    local_source: Optional[Path] = None,
    base_url: str = client.DEFAULT_BASE_URL,
    scope: str = SCOPE_CORE,
    dry_run: bool = False,
    target_version: Optional[str] = None,
    versions: Optional[Iterable[str]] = None,
) -> report.MigrationReport:
    """Replay all unconsumed CHANGES against `vault_root` in semver order.

    `target_version` overrides the "latest" lookup. `versions` overrides the
    full ordered list (mainly for tests). Otherwise version discovery prefers
    `local_source/.changelog/<scope_dir>/` and falls back to a one-shot
    `latest` from the HTTP version endpoint.
    """
    local = read_vault_version(vault_root)
    if versions is None:
        if local_source is not None:
            available = list_local_versions(local_source, scope=scope)
        else:
            info = client.fetch_version_info(base_url=base_url)
            latest = info.versions.get(scope) or info.core_version
            if latest is None:
                raise client.MigrationClientError("no version info available")
            available = [latest]
        if target_version is not None:
            available = [v for v in available if not _semver_gt(v, target_version)]
        if local is not None:
            ordered = [v for v in available if _semver_gt(v, local)]
        else:
            ordered = list(available)
    else:
        ordered = list(versions)

    to_version = ordered[-1] if ordered else local or "0.0.0"
    rpt = report.MigrationReport(from_version=local, to_version=to_version, dry_run=dry_run)
    if not ordered:
        rpt.results.append(report.EntryResult(
            version=to_version, handler="(none)", status="noop",
            summary="vault already at latest version",
        ))
        return rpt

    manifest = read_vault_manifest(vault_root)

    for v in ordered:
        bundle = client.load_bundle(v, scope=scope, local_source=local_source, base_url=base_url)
        parsed = parser.parse_change_file_text(bundle.payload_text, filename=f"v{v}.md")
        parser.validate_change_file(parsed)
        meta = parsed["meta"]
        excluded = (manifest or {}).get("excluded_paths", []) if manifest else []
        ctx = ApplyContext(
            vault_root=vault_root,
            source_root=bundle.source_root,
            manifest=manifest,
            excluded_paths=excluded,
            dry_run=dry_run,
        )
        for entry in meta["changes"]:
            rpt.results.extend(_apply_entry(entry, ctx, v))

    if not dry_run:
        bump_vault_version(vault_root, to_version)
        if manifest is not None:
            manifest["template_version"] = to_version
            manifest["last_applied_at"] = date.today().isoformat()
            write_vault_manifest(vault_root, manifest)

    return rpt


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m pipeline.migrations.applier",
        description="Replay template CHANGES against a vault.",
    )
    p.add_argument("vault", type=Path, help="Path to the vault root")
    p.add_argument("--local-source", type=Path,
                   help="Path to a local entropy-template/ checkout (offline mode).")
    p.add_argument("--base-url", default=client.DEFAULT_BASE_URL,
                   help="Webapp base URL (used when --local-source is absent).")
    p.add_argument("--scope", default=SCOPE_CORE,
                   help="Version scope: 'core' or 'role:<name>'.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the plan; do not touch files.")
    p.add_argument("--target-version",
                   help="Stop at this version instead of latest available.")
    p.add_argument("--no-report", action="store_true",
                   help="Skip writing outputs/migration-report-v*.md")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        rpt = apply(
            args.vault,
            local_source=args.local_source,
            base_url=args.base_url,
            scope=args.scope,
            dry_run=args.dry_run,
            target_version=args.target_version,
        )
    except (ValidationError, client.MigrationClientError) as e:
        print(f"applier: {e}", file=sys.stderr)
        return 2

    print(report.render_markdown(rpt))
    if not args.no_report:
        path = report.write_report(args.vault, rpt)
        print(f"\nreport: {path}", file=sys.stderr)
    return 1 if rpt.conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
