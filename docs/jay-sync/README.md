# Jay Sync

Tooling for keeping `entropy-template/` in sync with the upstream source of
truth at `github.com/jaykhalife/entropy`, and for replaying those changes
against existing user vaults.

## Read order

1. [changelog-discipline-skill.md](changelog-discipline-skill.md) — the contract
   we ask Jay's agent to follow. **This is the spec to give Jay.** It defines
   the `CHANGES/vX.Y.Z.md` format and the handler types.
2. [manifest-format.md](manifest-format.md) — the bot's bookkeeping file
   (`entropy-template/.jay-sync-manifest.json`) and how it's used.
3. [handlers.md](handlers.md) — the contract for each handler type:
   what frontmatter it accepts, what the bot does, what the applier does, and
   how it fails.

## Components

| Piece | Status | Location |
|---|---|---|
| Spec doc for Jay's agent | Built (this session) | `docs/jay-sync/changelog-discipline-skill.md` |
| Manifest format | Defined (this session) | `docs/jay-sync/manifest-format.md` |
| Handler reference | Defined (this session) | `docs/jay-sync/handlers.md` |
| Initial manifest | Built (this session) | `entropy-template/.jay-sync-manifest.json` |
| Bootstrap script | Built (this session) | `scripts/bootstrap_manifest.py` |
| Sync bot | Built (this session) | `scripts/sync_from_entropy.py` |
| GH Actions workflow | Built (this session) | `.github/workflows/sync-from-entropy.yml` |
| Migration applier (user-side upgrade) | **Not built** — next session | `pipeline/migrations/` (planned) |

## Flow

```
                ┌────────────────────────────────┐
                │  github.com/jaykhalife/entropy │
                │  (Jay's repo — source of truth)│
                └──────────────┬─────────────────┘
                               │ commits with CHANGES/vX.Y.Z.md
                               ▼
       ┌───────────────────────────────────────────────────┐
       │  GH Actions: .github/workflows/sync-from-entropy  │
       │  schedule: every 15 min + manual workflow_dispatch│
       └──────────────────────────┬────────────────────────┘
                                  │ runs scripts/sync_from_entropy.py
                                  ▼
       ┌───────────────────────────────────────────────────┐
       │  Bot reads CHANGES/v*.md, validates frontmatter,  │
       │  applies handlers to entropy-template/,           │
       │  updates manifest + TEMPLATE_VERSION.json         │
       └──────────────────────────┬────────────────────────┘
                                  │ gh pr create
                                  ▼
       ┌───────────────────────────────────────────────────┐
       │  PR in entropy-builder: sync/jay-vX.Y.Z           │
       │  Body: change summary, drift report, file diff    │
       │  Reviewer (David): approve & merge, or comment    │
       └──────────────────────────┬────────────────────────┘
                                  │ on merge
                                  ▼
       ┌───────────────────────────────────────────────────┐
       │  entropy-template/ is current.                    │
       │  Next vault build picks up the change.            │
       │  Returning users hit migration applier (future).  │
       └───────────────────────────────────────────────────┘
```

## What Jay needs to do

One-time:

1. Add `_skills/changelog-discipline.md` to his repo (copy of
   `docs/jay-sync/changelog-discipline-skill.md`).
2. Ensure his agent loads `_skills/changelog-discipline.md` on every session
   that touches tracked paths (`Portfolio Brain/_skills/`,
   `Portfolio Brain/_analytics/`, `Portfolio Brain/Company-Rules.md`).

Per change:

1. Make the change in the repo.
2. Write `CHANGES/vX.Y.Z.md` describing it (per the skill).
3. Commit both. Push.

The bot does the rest within ~15 minutes.
