"""Classifier methods for the structure_split handler.

Pure functions: given a file (frontmatter + filename) and the entry's classifier
config, return the destination path (relative, with trailing slash) or `None`
for `manual` (caller flags for human review).

Methods are the v0 set documented in docs/jay-sync/handlers.md:
participant_domain_majority, frontmatter_field_match, filename_regex, manual.
"""
import re
from pathlib import Path
from typing import Iterable, Optional

import yaml

from .schema import ValidationError


def _read_frontmatter(path: Path) -> dict:
    """Return YAML frontmatter as a dict, or {} if absent/malformed.

    Conservative: we never raise on a single file's bad frontmatter — the
    classifier just falls through to `default`. Bad classifier *config* still
    raises ValidationError up front.
    """
    try:
        raw = path.read_text()
    except OSError:
        return {}
    if not raw.startswith("---"):
        return {}
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return meta if isinstance(meta, dict) else {}


def _participant_emails(meta: dict) -> list[str]:
    """Extract participant emails. Accepts a list of strings or list of dicts
    with `email` keys, per handlers.md."""
    raw = meta.get("participants") or []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and isinstance(item.get("email"), str):
            out.append(item["email"])
    return out


def _domain(email: str) -> Optional[str]:
    at = email.rfind("@")
    return email[at + 1 :].lower() if at >= 0 else None


def _norm_dest(dest: str) -> str:
    return dest if dest.endswith("/") else dest + "/"


def classify_participant_domain_majority(
    file_path: Path,
    destinations: list[str],
    params: dict,
) -> str:
    internal = {d.lower() for d in (params.get("internal_domains") or [])}
    if not internal:
        raise ValidationError(
            "participant_domain_majority: missing/empty internal_domains"
        )
    threshold = params.get("threshold", 0.5)
    default = params.get("default")
    if len(destinations) < 2:
        raise ValidationError(
            "participant_domain_majority: needs at least 2 destinations (internal, external)"
        )

    meta = _read_frontmatter(file_path)
    emails = _participant_emails(meta)
    if not emails:
        if default is None:
            raise ValidationError(
                f"participant_domain_majority: {file_path.name} has no participants "
                "and no default destination configured"
            )
        return _norm_dest(default)

    matched = sum(1 for e in emails if (_domain(e) or "") in internal)
    fraction = matched / len(emails)
    chosen = destinations[0] if fraction >= threshold else destinations[1]
    return _norm_dest(chosen)


def classify_frontmatter_field_match(
    file_path: Path,
    destinations: list[str],
    params: dict,
) -> str:
    field = params.get("field")
    mapping = params.get("value_to_destination") or {}
    default = params.get("default")
    if not field or not isinstance(mapping, dict):
        raise ValidationError(
            "frontmatter_field_match: requires `field` and `value_to_destination`"
        )

    meta = _read_frontmatter(file_path)
    value = meta.get(field)
    dest = mapping.get(value) if value is not None else None
    if dest is None:
        if default is None:
            raise ValidationError(
                f"frontmatter_field_match: {file_path.name} field {field!r}={value!r} "
                "has no mapping and no default configured"
            )
        dest = default
    return _norm_dest(dest)


def classify_filename_regex(
    file_path: Path,
    destinations: list[str],
    params: dict,
) -> str:
    pattern_map = params.get("pattern_to_destination") or {}
    default = params.get("default")
    if not isinstance(pattern_map, dict) or not pattern_map:
        raise ValidationError(
            "filename_regex: requires non-empty `pattern_to_destination`"
        )

    name = file_path.name
    for pattern, dest in pattern_map.items():
        try:
            if re.search(pattern, name):
                return _norm_dest(dest)
        except re.error as e:
            raise ValidationError(
                f"filename_regex: invalid pattern {pattern!r}: {e}"
            ) from None
    if default is None:
        raise ValidationError(
            f"filename_regex: {name} matched no pattern and no default configured"
        )
    return _norm_dest(default)


_METHODS = {
    "participant_domain_majority": classify_participant_domain_majority,
    "frontmatter_field_match": classify_frontmatter_field_match,
    "filename_regex": classify_filename_regex,
}


def classify(
    file_path: Path,
    classifier: dict,
    destinations: list[str],
) -> Optional[str]:
    """Dispatch. Returns destination dir (with trailing /) or None for manual."""
    method = classifier.get("method")
    if method == "manual":
        return None
    fn = _METHODS.get(method)
    if fn is None:
        raise ValidationError(f"unknown classifier method {method!r}")
    return fn(file_path, destinations, classifier.get("params") or {})


def iter_files(root: Path) -> Iterable[Path]:
    """Yield files (not dirs) under root, sorted for deterministic reports."""
    if not root.is_dir():
        return
    yield from sorted(p for p in root.rglob("*") if p.is_file())
