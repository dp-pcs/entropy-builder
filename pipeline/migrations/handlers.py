"""Handler implementations for CHANGES entries.

These functions are written for the template-side bot today; the future vault
applier (bd-ez3) will add conflict-aware wrappers/branches around them or call
the same building blocks with vault-specific semantics. Either way, parsing,
validation, path utilities, and schema live in sibling modules so both sides
share them and cannot drift.

Every handler is parameterized on `target_root` (the directory being mutated)
and `source_root` where it reads from (Jay's repo clone, or — eventually — a
migration payload checkout). No module-level globals.
"""
import shutil
from pathlib import Path

from .paths import path_is_excluded, path_is_tracked, sha256_of_path
from .schema import ValidationError


def apply_rename(
    entry: dict,
    manifest: dict,
    dry_run: bool,
    *,
    target_root: Path,
) -> list[str]:
    src_rel = entry["from"].rstrip("/")
    dst_rel = entry["to"].rstrip("/")
    excluded = manifest.get("excluded_paths", [])
    if path_is_excluded(src_rel, excluded) and path_is_excluded(dst_rel, excluded):
        return [f"skipped (excluded): rename {src_rel} -> {dst_rel}"]
    if path_is_excluded(src_rel, excluded) or path_is_excluded(dst_rel, excluded):
        raise ValidationError(
            f"rename: {src_rel!r} -> {dst_rel!r} crosses exclusion boundary; "
            "split into delete_file + add_file or adjust excluded_paths"
        )
    src_abs = target_root / src_rel
    dst_abs = target_root / dst_rel
    if not src_abs.exists():
        raise ValidationError(f"rename: source {src_rel!r} does not exist in template")
    if dst_abs.exists():
        raise ValidationError(f"rename: destination {dst_rel!r} already exists in template")
    if not dry_run:
        dst_abs.parent.mkdir(parents=True, exist_ok=True)
        src_abs.rename(dst_abs)
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


def apply_add_file(
    entry: dict,
    source_root: Path,
    manifest: dict,
    version: str,
    dry_run: bool,
    *,
    target_root: Path,
) -> list[str]:
    rel = entry["path"]
    if path_is_excluded(rel, manifest.get("excluded_paths", [])):
        return [f"skipped (excluded): {rel}"]
    if not path_is_tracked(rel, manifest["tracked_paths"]):
        raise ValidationError(f"add_file: {rel!r} is outside tracked_paths; widen tracked_paths or fix the entry")
    src = source_root / rel
    if not src.is_file():
        raise ValidationError(f"add_file: {rel!r} does not exist in source at this commit")
    dst = target_root / rel
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    manifest["files"][rel] = {
        "source_sha256": sha256_of_path(src),
        "dest_path_in_template": f"entropy-template/{rel}",
        "first_seen_version": version,
        "last_updated_version": version,
    }
    return [f"added {rel}"]


def apply_delete_file(
    entry: dict,
    manifest: dict,
    dry_run: bool,
    *,
    target_root: Path,
) -> list[str]:
    rel = entry["path"]
    if path_is_excluded(rel, manifest.get("excluded_paths", [])):
        return [f"skipped (excluded): {rel}"]
    if rel not in manifest["files"]:
        raise ValidationError(f"delete_file: {rel!r} not in manifest")
    target = target_root / rel
    if not dry_run and target.exists():
        target.unlink()
    del manifest["files"][rel]
    return [f"deleted {rel}"]


def apply_content_patch(
    entry: dict,
    source_root: Path,
    manifest: dict,
    version: str,
    dry_run: bool,
    *,
    target_root: Path,
) -> list[str]:
    rel = entry["path"]
    if path_is_excluded(rel, manifest.get("excluded_paths", [])):
        return [f"skipped (excluded): {rel}"]
    if rel not in manifest["files"]:
        raise ValidationError(f"content_patch: {rel!r} not in manifest; add_file first")
    src = source_root / rel
    if not src.is_file():
        raise ValidationError(f"content_patch: {rel!r} missing in source at this commit")
    dst = target_root / rel
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    manifest["files"][rel]["source_sha256"] = sha256_of_path(src)
    manifest["files"][rel]["last_updated_version"] = version
    return [f"patched {rel}"]


def apply_structure_split(
    entry: dict,
    manifest: dict,
    *,
    target_root: Path,
) -> list[str]:
    """Bot-side: just create the destination folders + flag for human review.

    The actual per-file classification happens in the migration applier
    (runs against user vaults). For the entropy-template/ side, the bot leaves
    files in place — entropy-template/ is a template, not user data, so there's
    nothing to classify yet. The entry is recorded so user-side applier can
    replay it later.
    """
    src_rel = entry["from"].rstrip("/")
    if path_is_excluded(src_rel, manifest.get("excluded_paths", [])):
        return [f"skipped (excluded): structure_split from {src_rel}"]
    src_abs = target_root / src_rel
    affected = [f"structure_split: {src_rel} -> {entry['to']} (recorded; applies to user vaults only)"]
    if src_abs.is_dir():
        affected.append(f"  ({src_rel} exists in template — no per-file moves needed at template level)")
    return affected


def apply_change_entry(
    entry: dict,
    source_root: Path,
    manifest: dict,
    version: str,
    dry_run: bool,
    *,
    target_root: Path,
) -> list[str]:
    handler = entry["type"]
    if handler == "rename":
        return apply_rename(entry, manifest, dry_run, target_root=target_root)
    if handler == "add_file":
        return apply_add_file(entry, source_root, manifest, version, dry_run, target_root=target_root)
    if handler == "delete_file":
        return apply_delete_file(entry, manifest, dry_run, target_root=target_root)
    if handler == "content_patch":
        return apply_content_patch(entry, source_root, manifest, version, dry_run, target_root=target_root)
    if handler == "structure_split":
        return apply_structure_split(entry, manifest, target_root=target_root)
    raise ValidationError(f"unknown handler {handler!r}")  # belt-and-suspenders
