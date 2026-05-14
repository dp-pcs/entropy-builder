# Jay-Sync Manifest Format

The manifest at `entropy-template/.jay-sync-manifest.json` is the bot's
bookkeeping of what we mirror from Jay's repo. It lets the sync bot answer
two questions on every run:

1. What files are we tracking, and what was their content the last time we synced?
2. What CHANGES entries have we already ingested?

## Schema

```json
{
  "schema_version": 1,
  "source_repo": "jaykhalife/entropy",
  "source_branch": "main",
  "last_synced_commit": "8efff94abc123...",
  "last_synced_at": "2026-05-13T23:30:00Z",
  "tracked_paths": [
    "Portfolio Brain/_skills/",
    "Portfolio Brain/_analytics/",
    "Portfolio Brain/Company-Rules.md"
  ],
  "excluded_paths": [
    "Portfolio Brain/_skills/changelog-discipline.md"
  ],
  "files": {
    "Portfolio Brain/_skills/ingestion.md": {
      "source_sha256": "abc123...",
      "dest_path_in_template": "entropy-template/Portfolio Brain/_skills/ingestion.md",
      "first_seen_version": "1.0.0",
      "last_updated_version": "1.1.0"
    }
  },
  "ingested_changes": [
    {
      "version": "1.0.0",
      "ingested_at": "2026-05-01T00:00:00Z",
      "source_commit": "ad80abf..."
    },
    {
      "version": "1.1.0",
      "ingested_at": "2026-05-13T16:00:00Z",
      "source_commit": "f00ba12..."
    }
  ]
}
```

## Field reference

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | int | Bump if we change this format incompatibly |
| `source_repo` | string | GitHub `owner/name`; bot uses it to clone |
| `source_branch` | string | Branch we follow (always `main` for now) |
| `last_synced_commit` | string | Commit SHA we last processed; bot only looks at changes after this |
| `last_synced_at` | ISO string | Wall-clock for human inspection |
| `tracked_paths` | string[] | Path prefixes/files we mirror. Anything in Jay's repo outside these is ignored. Trailing `/` means "directory contents, recursive." |
| `excluded_paths` | string[] | Path prefixes/files inside `tracked_paths` that we explicitly do NOT mirror into `entropy-template/`. Used for operational files (e.g., `changelog-discipline.md` itself — relevant in Jay's repo, irrelevant to end users). Same prefix-with-`/` semantics as `tracked_paths`. |
| `files` | object | One entry per mirrored file with its source content hash. Excluded files are never added here. |
| `files[path].source_sha256` | string | SHA-256 of Jay's copy at last sync. Bot uses this to detect content drift even when no CHANGES entry was written (defensive) |
| `ingested_changes` | object[] | History of every CHANGES/vX.Y.Z.md we've processed |

## How the bot uses it

On each run:

1. Read `last_synced_commit` from the manifest.
2. `gh api repos/jaykhalife/entropy/commits` to find newer commits.
3. For each new commit, check whether it touched `CHANGES/v*.md` or any
   `tracked_paths`.
4. For each new `CHANGES/v*.md` not in `ingested_changes`:
   - Parse the frontmatter; validate against the handler schema.
   - For each entry in `changes:`, apply the file-level change to
     `entropy-template/` (rename, add, delete, copy, patch).
   - Append the entry to `TEMPLATE_VERSION.json` history.
   - Recompute `source_sha256` for affected files in `files`.
   - Append to `ingested_changes`.
5. Defensive check: if any `tracked_paths` file has changed in Jay's repo since
   our last hash but **no** `CHANGES/v*.md` covers it, flag the drift in the PR
   description so the reviewer can either accept it or ask Jay to write the
   missing entry.
6. Commit the modified manifest + template files on a `sync/jay-vX.Y.Z` branch
   and open a PR via `gh pr create`.

## Drift detection

The bot intentionally tracks `source_sha256` for every file even though
`CHANGES/*.md` is supposed to be authoritative. Two reasons:

- **Forgotten CHANGES files:** Jay (or his agent) makes a structural change
  without writing the entry. Without hash tracking we'd silently miss it.
- **Reseller-style soft errors:** Jay edits Company-Rules.md but doesn't think
  it warrants a CHANGES entry. The hash check catches it; the PR reviewer
  decides whether to back-fill an entry or merge as-is.

When drift is detected, the PR body includes a section like:

```
## Drift detected (no CHANGES entry covers these)
- Portfolio Brain/Company-Rules.md  (hash changed, no v* entry)
- Portfolio Brain/_skills/triage.md (hash changed, no v* entry)

Ask Jay to write a CHANGES/v1.x.x.md describing these, or merge as-is and
they'll be untracked.
```

The reviewer's job is to decide which path to take.

## Bootstrap

On first run, `files{}` is empty and `last_synced_commit` is the empty string.
The bootstrap script (`scripts/bootstrap_manifest.py`, run once manually)
populates the manifest by hashing the current `entropy-template/` contents and
records the current Jay-repo HEAD as `last_synced_commit`. Subsequent runs only
see *changes after* bootstrap, so we don't get a flood of false drift.
