---
name: changelog-discipline
description: Write a CHANGES/vX.Y.Z.md file whenever you modify the structure of this vault (rename, add, delete, restructure, or substantively patch a tracked file). The file is consumed downstream by an automated sync bot that mirrors changes into entropy_builder and replays them against existing user vaults. Without the file, downstream tooling cannot apply the change — so this discipline is required, not optional.
---

# Changelog Discipline

This skill exists because Jay's Entropy repo is the upstream source of truth for
many downstream user vaults. When the structure changes here, an automated bot
in `entropy_builder` copies the change into the template and replays it against
returning users' vaults so they don't drift. The bot can only do this if you
write a `CHANGES/vX.Y.Z.md` file alongside the change describing **what** changed
and, when content-aware, **how** to classify/move existing data.

If you skip the file, the change is invisible to downstream tooling. Don't skip it.

## When to apply

Write a `CHANGES/*.md` entry any time you do **any** of the following inside the
tracked directories (`Portfolio Brain/_skills/`, `Portfolio Brain/_analytics/`,
`Portfolio Brain/Company-Rules.md`):

- **Rename** a file or folder
- **Add** a new file (new skill, new analytics doc)
- **Delete** a file
- **Split** a folder into sub-folders that require classifying existing content
- **Substantively edit** an existing file (not typo fixes — material changes
  to instructions, schema, or behavior)

If you're unsure whether a change is structural, write the entry. False positives
are cheap; false negatives silently break user vaults.

## File location and naming

- Location: `CHANGES/` at the repo root (create if it doesn't exist)
- Name: `vMAJOR.MINOR.PATCH.md` following semver
  - **MAJOR** — breaking restructure (e.g., split a folder, change required frontmatter)
  - **MINOR** — additive (new skill, new section) or rename without content move
  - **PATCH** — in-place edit of existing file content

Look at the highest existing `CHANGES/v*.md` before naming yours.

## File format

YAML frontmatter (machine-read by the bot) + prose (human-read in the PR
description and end-user changelog).

```markdown
---
version: 1.2.0
date: 2026-05-14
type: minor                # major | minor | patch
summary: One-line summary used in PR title and CHANGELOG
changes:
  - type: <handler>        # see "Handler types" below
    ...handler-specific fields...
    rationale: "Why this change"
---

# v1.2.0 — Human-readable title

Prose explanation. What did you change and why. If a change is content-aware
(needs to classify or move existing user data), explain the classifier in plain
English here so a human reviewer can verify the structured `classifier:` block
in the frontmatter is correct.
```

The frontmatter must validate against the schema in
`entropy_builder/docs/jay-sync/manifest-format.md`. If you're unsure, ask before
committing.

## Handler types (v0)

Four handlers are supported on day one. Use exactly one `type:` per change entry.

### 1. `rename`

Rename a single file or folder. Pure path change, no content transformation.

```yaml
- type: rename
  from: Entropy/
  to: Portfolio Brain/
  rationale: "Cosmetic rebrand — name better reflects intent"
```

End-user effect: their `Entropy/` directory is renamed to `Portfolio Brain/`.
All wikilinks `[[Entropy/...]]` get rewritten to `[[Portfolio Brain/...]]`.

### 2. `add_file`

Introduce a new tracked file. The actual file content lives in the same commit;
the entry just declares its existence.

```yaml
- type: add_file
  path: Portfolio Brain/_skills/scenario-modeling.md
  rationale: "New workflow for what-if analysis on at-risk accounts"
```

End-user effect: file is copied into their vault at the same path.

### 3. `delete_file`

Remove a tracked file from the template. Existing user copies are deleted on
upgrade — be sure this is what you want.

```yaml
- type: delete_file
  path: Portfolio Brain/_skills/old-deprecated-skill.md
  rationale: "Replaced by triage.md in v1.1.0; no longer maintained"
```

End-user effect: file is deleted from their vault. If they edited it locally,
the bot will flag the conflict in the PR rather than silently nuking it.

### 4. `structure_split`

Split one folder into multiple sub-folders, classifying each existing file
into the right destination. **This is the only handler where you must describe
a classifier.**

```yaml
- type: structure_split
  from: Portfolio Brain/Meetings/
  to:
    - Portfolio Brain/Meetings/Internal/
    - Portfolio Brain/Meetings/External/
  classifier:
    method: participant_domain_majority
    params:
      internal_domains: [trilogy.com, aurea.com, skyvera.com]
      threshold: 0.5
      default: External    # if classifier can't decide, where does the file land
  rationale: "Separate internal team syncs from customer meetings"
```

Allowed `classifier.method` values for v0:

| Method | What it does | Required params |
|---|---|---|
| `participant_domain_majority` | Reads `participants` frontmatter, computes fraction of internal-domain emails, routes by threshold | `internal_domains`, `threshold`, `default` |
| `frontmatter_field_match` | Routes by exact match on a frontmatter field value | `field`, `value_to_destination` (dict), `default` |
| `filename_regex` | Routes by regex against the filename | `pattern_to_destination` (dict), `default` |
| `manual` | No automatic classification — bot opens a PR with each file flagged for human routing | (none) |

If your classifier needs something not in the list, set `method: manual` and
explain the logic in prose. The downstream review will catch it and extend the
handler library if it's a recurring pattern.

### 5. `content_patch` (v0)

Substantive in-place edit to an existing tracked file. The bot detects this
automatically when a file's hash changes without a rename, but you should still
write the entry to document **why** the edit matters.

```yaml
- type: content_patch
  path: Portfolio Brain/Company-Rules.md
  rationale: "Clarified Tier-2 escalation rules for at-risk renewals"
```

End-user effect: file is overwritten with the new content. If the user edited
it locally, the bot flags a conflict in the PR.

## Workflow

1. Plan the change in your head: which tracked files does it touch?
2. Make the actual content changes in the repo (rename folder, add file, edit
   Company-Rules.md, whatever).
3. Pick the next semver number based on the highest existing `CHANGES/v*.md`
   and the type of change you made.
4. Write `CHANGES/vX.Y.Z.md` describing each change with the correct handler.
5. Run a sanity check: does each entry reference a file path that actually
   exists (for `add_file`, `content_patch`, `rename:to`) or used to exist
   (for `delete_file`, `rename:from`, `structure_split:from`)?
6. Commit the actual file changes + the `CHANGES/vX.Y.Z.md` in the same commit.
7. Push.

The entropy_builder sync bot runs on a 15-minute schedule, picks up your
`CHANGES/*.md`, and opens a PR mirroring the change into the template. A human
reviews the PR before it merges — if anything looks off, you'll get a comment.

## Anti-patterns

- **Don't bundle unrelated changes** in one `CHANGES/vX.Y.Z.md`. One semantic
  change per file. If you rename a folder AND add a new skill, write two entries
  in the same file's `changes:` list, but don't write "v1.2.0 — random edits."
- **Don't bump versions backward.** If `v1.2.0` exists, your next file is
  `v1.2.1` or `v1.3.0`, never `v1.1.5`.
- **Don't describe classifier logic only in prose.** The bot reads frontmatter,
  not prose. If you wrote "and we classify by checking the participants" but
  the frontmatter has no `classifier:` block, the migration silently runs as
  `manual` and stalls in human review.
- **Don't write CHANGES entries for content you don't want copied to users.**
  Working notes, drafts, sandbox skills — keep those outside `_skills/` and
  `_analytics/` so the bot ignores them.

## Quick reference: what to write for common changes

| You did this | Handler | Required frontmatter fields |
|---|---|---|
| Renamed a folder | `rename` | `from`, `to`, `rationale` |
| Added a new skill | `add_file` | `path`, `rationale` |
| Deleted an old skill | `delete_file` | `path`, `rationale` |
| Split a folder, files need classifying | `structure_split` | `from`, `to`, `classifier`, `rationale` |
| Edited Company-Rules.md substantially | `content_patch` | `path`, `rationale` |
| Just fixed a typo | (nothing — no CHANGES file needed) | |
