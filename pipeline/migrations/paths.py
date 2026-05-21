"""Path predicates + hashing utilities shared between bot and applier."""
import hashlib
from pathlib import Path


def sha256_of_path(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def path_is_tracked(path: str, tracked_paths: list[str]) -> bool:
    for tp in tracked_paths:
        if tp.endswith("/") and path.startswith(tp):
            return True
        if path == tp:
            return True
    return False


def path_is_excluded(path: str, excluded_paths: list[str] | None) -> bool:
    """A path is excluded if it exactly matches an exclude entry, or starts with
    one whose entry ends in '/' (directory exclude).
    """
    for ep in excluded_paths or []:
        if ep.endswith("/") and path.startswith(ep):
            return True
        if path == ep:
            return True
    return False
