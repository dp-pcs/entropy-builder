# Migration Handlers (v0)

This document defines the runtime contract for each handler type the bot
recognizes. It is the source of truth for both:

- The sync bot, which validates `CHANGES/*.md` frontmatter against this schema
  and applies the file-level change to `entropy-template/`
- The eventual migration applier (separate, not built in this session), which
  replays the same handlers against returning users' vault directories

Adding a new handler is a deliberate cross-cutting change: schema here, bot
validator update, applier implementation, end-to-end test.

## Common fields

Every entry in `CHANGES/*.md` `changes:` has these:

| Field | Required | Notes |
|---|---|---|
| `type` | yes | One of the handler names below |
| `rationale` | yes | Free-text "why"; appears in PR body and user-facing CHANGELOG |

Handler-specific fields are listed under each handler below.

## `rename`

Rename a file or folder. Path-only — no content transformation.

**Frontmatter:**
```yaml
- type: rename
  from: <old path, relative to repo root>
  to: <new path, relative to repo root>
  rationale: "..."
```

**Bot behavior:**
- Asserts `from` exists in template (pre-change) and `to` does not
- `git mv from to` inside `entropy-template/`
- Updates all manifest entries whose path starts with `from` to start with `to`

**Applier behavior (future):**
- Same `git mv` against user's vault
- Rewrite wikilinks `[[from/...]]` → `[[to/...]]` in every `.md` file across the
  vault (regex with word-boundary guard)

**Failure modes:**
- `to` already exists → bot aborts, flags conflict in PR
- `from` doesn't exist → bot aborts; Jay's CHANGES entry references a path
  that wasn't in the repo

## `add_file`

Add a new tracked file.

**Frontmatter:**
```yaml
- type: add_file
  path: <new path, relative to repo root>
  rationale: "..."
```

**Bot behavior:**
- Reads file content from Jay's repo at `path`
- Writes it to `entropy-template/<path>`
- Adds an entry to manifest `files{}` with current hash

**Applier behavior:**
- Writes the file into user's vault at the same path
- If user already has a file at that path (rare — possible if they manually
  created one), preserves theirs and reports a conflict

**Failure modes:**
- `path` doesn't exist in Jay's repo at the synced commit → bot aborts
- `path` is outside `tracked_paths` → bot aborts; Jay added a file in a
  directory we don't mirror (probably intentional — they should narrow the
  CHANGES entry or expand tracked_paths)

## `delete_file`

Remove a tracked file.

**Frontmatter:**
```yaml
- type: delete_file
  path: <path, relative to repo root>
  rationale: "..."
```

**Bot behavior:**
- Removes `entropy-template/<path>`
- Removes the entry from manifest `files{}`

**Applier behavior:**
- If user's file matches the last-known hash → delete it
- If user's file has diverged → preserve it, report "kept your local copy
  of <path> which is no longer in the template; review and delete manually
  if appropriate"

**Failure modes:**
- `path` not in manifest → bot aborts; Jay deleted something we weren't tracking

## `structure_split`

Split one folder into sub-folders, classifying each existing file into the
correct destination. This is the only handler that needs a runtime classifier.

**Frontmatter:**
```yaml
- type: structure_split
  from: <existing folder path, ending with />
  to:
    - <destination folder 1, ending with />
    - <destination folder 2, ending with />
    - ...
  classifier:
    method: <one of the methods below>
    params:
      <method-specific params>
  rationale: "..."
```

**Allowed `classifier.method` values:**

### `participant_domain_majority`

Reads each file's `participants` frontmatter field (expected to be a list of
emails or a list of objects with `email` keys), computes the fraction whose
domain matches `internal_domains`, and routes by `threshold`.

```yaml
classifier:
  method: participant_domain_majority
  params:
    internal_domains: [trilogy.com, aurea.com, skyvera.com]
    threshold: 0.5            # ≥ this fraction internal → first destination
    default: <destination>    # fallback when participants field missing/empty
```

Destinations in order: index `0` = internal, index `1` = external. (Generalize
later if we ever need 3+ buckets.)

### `frontmatter_field_match`

Routes by exact match on a named frontmatter field.

```yaml
classifier:
  method: frontmatter_field_match
  params:
    field: customer_tier
    value_to_destination:
      HVO: <destination folder>
      At-Risk: <destination folder>
      Standard: <destination folder>
    default: <destination>
```

### `filename_regex`

Routes by regex against the filename (not the full path).

```yaml
classifier:
  method: filename_regex
  params:
    pattern_to_destination:
      "^Internal_": <destination>
      "_QBR\\.md$": <destination>
    default: <destination>
```

Patterns are tried in order; first match wins.

### `manual`

No automatic classification. Bot opens the PR with each file flagged for a
human reviewer to route. Use when the classification logic is too project-
specific to express in the v0 method library — and propose adding a new method
if it recurs.

```yaml
classifier:
  method: manual
```

**Bot behavior (structure_split):**
- Asserts `from` exists and contains files; asserts each `to` does not exist
- Creates each `to` directory
- For each file in `from`, runs the classifier; moves to the chosen destination
- Updates manifest entries for affected paths
- PR body includes a per-file breakdown so the reviewer can spot mis-classifications

**Applier behavior:**
- Same logic against user's vault directory
- Per-file report at the end so the user knows what moved where

**Failure modes:**
- Classifier method unknown → bot aborts (the schema check catches this
  before any files move)
- Classifier params malformed → bot aborts

## `content_patch`

Substantive in-place edit of an existing tracked file.

**Frontmatter:**
```yaml
- type: content_patch
  path: <path, relative to repo root>
  rationale: "..."
```

**Bot behavior:**
- Copies new content from Jay's repo at `path` over `entropy-template/<path>`
- Updates the hash in manifest

**Applier behavior:**
- If user's local hash matches our last-known source hash → overwrite with new
  content
- If user's local hash differs → they edited it locally. Preserve theirs, write
  the template version as `<path>.new` next to it, and report the conflict

**Failure modes:**
- `path` not in manifest → bot aborts; the file isn't being tracked (Jay
  should add an `add_file` entry first, or expand `tracked_paths`)

## Drift entries (auto-generated)

When the bot detects file changes without a covering CHANGES entry, it
synthesizes a virtual `drift` entry in the PR description (not in
`TEMPLATE_VERSION.json`). These are not real handlers — they're a signal to
the human reviewer that something needs attention. The reviewer either:

- Asks Jay to write a proper CHANGES entry retroactively
- Merges the PR with the file changes but acknowledges the entries are
  untracked (recorded in the PR description as an audit trail)

Drift entries never make it into the applier — only proper handler entries do.
