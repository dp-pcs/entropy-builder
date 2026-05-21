"""Schema constants for CHANGES/*.md frontmatter validation."""
import re

VALID_HANDLERS = {"rename", "add_file", "delete_file", "structure_split", "content_patch"}

VALID_CLASSIFIERS = {
    "participant_domain_majority",
    "frontmatter_field_match",
    "filename_regex",
    "manual",
}

SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)\.md$")

# Scope vocabulary for multi-axis versioning (see [[entropy-versioning]] memory).
# A CHANGES file's `scope:` field is either 'core' (applies to every vault) or
# 'role:<role-name>' (applies only to vaults whose user_role matches). Omitted
# scope defaults to 'core' for backward-compat with pre-2026-05-20 CHANGES files.
SCOPE_CORE = "core"
ROLE_SCOPE_RE = re.compile(r"^role:[a-z0-9][a-z0-9_-]*$")


def is_valid_scope(scope: str) -> bool:
    return scope == SCOPE_CORE or bool(ROLE_SCOPE_RE.match(scope))


class ValidationError(Exception):
    pass
