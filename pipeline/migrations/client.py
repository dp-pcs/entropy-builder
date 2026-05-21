"""Migration payload client.

Two responsibilities:

1. Talk to the webapp endpoints (`/api/template/version`, `/api/migrations/{version}`,
   `/api/template/archive`) for the version signal, CHANGES text, and file bodies.
2. Provide a `--local-source` escape hatch that points at a local
   `entropy-template/` checkout, so the applier can be exercised end-to-end
   without depending on a running webapp.

The applier resolves file bodies via a `source_root: Path`. In `--local-source`
mode that's the checkout directly; in HTTP mode the orchestrator fetches
`/api/template/archive`, extracts to a temp dir, and uses that as the
synthetic source_root (matches local-source semantics 1:1).
"""
from __future__ import annotations

import io
import json
import tarfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .schema import ROLE_SCOPE_RE, SCOPE_CORE, ValidationError


DEFAULT_BASE_URL = "https://entropy.elelem.expert"


class MigrationClientError(Exception):
    """Network / endpoint failure (kept distinct from ValidationError)."""


@dataclass
class VersionInfo:
    """Subset of `/api/template/version` we care about for replay planning."""

    core_version: Optional[str]
    versions: dict[str, str]  # {"core": "1.2.3", "role:ic-sales": "0.4.0", ...}
    role_pack_version: Optional[str] = None  # populated when fetched with role=

    @classmethod
    def from_response(cls, data: dict) -> "VersionInfo":
        versions = dict(data.get("versions") or {})
        core = versions.get("core") or data.get("core_version")
        pack = (data.get("role_pack") or {}).get("version")
        if pack and "role" in (data.get("role_pack") or {}):
            versions[f"role:{data['role_pack']['role']}"] = pack
        return cls(core_version=core, versions=versions, role_pack_version=pack)


@dataclass
class MigrationBundle:
    """One version of CHANGES + the source tree to read file bodies from.

    `payload_text` is the raw `CHANGES/vX.Y.Z.md` text (the applier parses it
    with the same `parser` the bot uses). `source_root` is a directory whose
    layout matches `entropy-template/` (or Jay's repo) so handlers can locate
    file bodies by relative path.
    """

    version: str
    scope: str
    payload_text: str
    source_root: Path


# -----------------------------------------------------------------------------
# HTTP fetchers
# -----------------------------------------------------------------------------


def _http_get(url: str, *, timeout: float = 10.0) -> tuple[bytes, str]:
    """Fetch a URL and return (body, content_type). Raises MigrationClientError."""
    req = urllib.request.Request(url, headers={"User-Agent": "entropy-applier/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 — controlled base_url
            return resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        raise MigrationClientError(f"GET {url} → HTTP {e.code} {e.reason}") from None
    except urllib.error.URLError as e:
        raise MigrationClientError(f"GET {url} → {e.reason}") from None


def fetch_version_info(
    base_url: str = DEFAULT_BASE_URL,
    role: Optional[str] = None,
) -> VersionInfo:
    suffix = f"?role={role}" if role else ""
    url = f"{base_url.rstrip('/')}/api/template/version{suffix}"
    body, _ = _http_get(url)
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise MigrationClientError(f"version endpoint returned non-JSON: {e}") from None
    return VersionInfo.from_response(data)


def fetch_migration_payload_text(
    version: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    scope: str = SCOPE_CORE,
) -> str:
    _validate_scope(scope)
    url = f"{base_url.rstrip('/')}/api/migrations/{version}?scope={scope}"
    body, _ = _http_get(url)
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as e:
        raise MigrationClientError(f"migration payload not UTF-8: {e}") from None


def fetch_template_archive(base_url: str = DEFAULT_BASE_URL) -> bytes:
    """Fetch the gzipped tar of entropy-template/ from the webapp."""
    url = f"{base_url.rstrip('/')}/api/template/archive"
    body, _ = _http_get(url, timeout=30.0)
    return body


def extract_template_archive(archive_bytes: bytes, dest: Path) -> None:
    """Extract a gzipped tar into `dest`. Refuses absolute or parent-escaping paths."""
    dest.mkdir(parents=True, exist_ok=True)
    try:
        tar = tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz")
    except tarfile.TarError as e:
        raise MigrationClientError(f"template archive is not a valid tar.gz: {e}") from None
    with tar:
        for member in tar.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise MigrationClientError(f"unsafe member path in archive: {member.name!r}")
        # Python 3.12+ has a `filter` arg; tolerate older runtimes by extracting all.
        try:
            tar.extractall(dest, filter="data")  # type: ignore[arg-type]
        except TypeError:
            tar.extractall(dest)


# -----------------------------------------------------------------------------
# Local-source path (offline / testing)
# -----------------------------------------------------------------------------


def local_version_info(local_source: Path) -> VersionInfo:
    """Read version info from a local entropy-template checkout's TEMPLATE_VERSION.json."""
    tv = local_source / "TEMPLATE_VERSION.json"
    if not tv.is_file():
        raise MigrationClientError(f"--local-source missing TEMPLATE_VERSION.json: {tv}")
    data = json.loads(tv.read_text())
    versions = dict(data.get("versions") or {})
    core = versions.get("core") or data.get("version")
    return VersionInfo(core_version=core, versions=versions or {"core": core})


def local_migration_payload_text(
    local_source: Path,
    version: str,
    *,
    scope: str = SCOPE_CORE,
) -> str:
    _validate_scope(scope)
    scope_dir = scope.replace(":", "-")
    path = local_source / ".changelog" / scope_dir / f"v{version}.md"
    if not path.is_file():
        raise MigrationClientError(
            f"--local-source missing CHANGES for {scope}@v{version}: {path}"
        )
    return path.read_text()


# -----------------------------------------------------------------------------
# Bundle (high-level: payload text + the source_root for file bodies)
# -----------------------------------------------------------------------------


def load_bundle(
    version: str,
    *,
    scope: str = SCOPE_CORE,
    local_source: Path,
    base_url: str = DEFAULT_BASE_URL,
) -> MigrationBundle:
    """Return a MigrationBundle for one version.

    `local_source` is required: either a real checkout (`--local-source`) or
    the temp dir the orchestrator created by extracting `/api/template/archive`.
    Payload text comes from the same directory's `.changelog/` — the archive
    includes it, so HTTP mode and offline mode are symmetric.
    """
    payload_text = local_migration_payload_text(local_source, version, scope=scope)
    return MigrationBundle(
        version=version,
        scope=scope,
        payload_text=payload_text,
        source_root=local_source,
    )


def _validate_scope(scope: str) -> None:
    if scope == SCOPE_CORE:
        return
    if scope.startswith("role:") and ROLE_SCOPE_RE.match(scope):
        return
    raise ValidationError(f"invalid scope {scope!r}; want 'core' or 'role:<name>'")
