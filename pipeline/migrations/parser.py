"""Parse + validate CHANGES/vX.Y.Z.md files.

Output of `parse_change_file` is a dict {meta, prose, filename}. `meta['scope']`
is always populated (defaults to 'core' when frontmatter omits it).
"""
from datetime import date, datetime
from pathlib import Path

import yaml

from .schema import (
    SCOPE_CORE,
    SEMVER_RE,
    VALID_CLASSIFIERS,
    VALID_HANDLERS,
    ValidationError,
    is_valid_scope,
)


def stringify_dates(obj):
    """Recursively convert datetime.date / datetime instances to ISO strings.

    PyYAML parses unquoted YYYY-MM-DD as datetime.date, which json.dumps can't
    serialize. We normalize before writing anything derived from frontmatter.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()[:10] if isinstance(obj, date) and not isinstance(obj, datetime) else obj.isoformat()
    if isinstance(obj, dict):
        return {k: stringify_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [stringify_dates(v) for v in obj]
    return obj


def list_change_files(repo: Path, changes_dir: str = "CHANGES") -> list[Path]:
    target = repo / changes_dir
    if not target.is_dir():
        return []
    return sorted([p for p in target.glob("v*.md") if SEMVER_RE.match(p.name)])


def parse_change_file_text(raw: str, *, filename: str) -> dict:
    """Parse a CHANGES file from its raw text. Used by the applier when payloads
    come from HTTP or another in-memory source."""
    if not raw.startswith("---"):
        raise ValidationError(f"{filename}: missing YAML frontmatter")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValidationError(f"{filename}: malformed frontmatter (no closing ---)")
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise ValidationError(f"{filename}: YAML parse error: {e}") from None
    if not isinstance(meta, dict):
        raise ValidationError(f"{filename}: frontmatter is not a mapping")
    meta = stringify_dates(meta)
    meta.setdefault("scope", SCOPE_CORE)
    prose = parts[2].strip()
    return {"meta": meta, "prose": prose, "filename": filename}


def parse_change_file(path: Path) -> dict:
    return parse_change_file_text(path.read_text(), filename=path.name)


def validate_change_entry(filename: str, entry: dict, idx: int) -> None:
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


def validate_change_file(parsed: dict) -> None:
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
    scope = meta.get("scope", SCOPE_CORE)
    if not is_valid_scope(scope):
        raise ValidationError(
            f"{filename}: invalid scope {scope!r} — must be 'core' or 'role:<name>'"
        )
    changes = meta.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ValidationError(f"{filename}: 'changes' must be a non-empty list")
    for i, entry in enumerate(changes):
        validate_change_entry(filename, entry, i)
