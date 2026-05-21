# MEMORY.md

> Persistent long-term memory. Append-only in spirit. Never overwrite from scratch.

## Rules (for the agent)

1. Append new facts; never rewrite the whole file.
2. Organize by section (Facts / Decisions / People / Context). Add sections as needed.
3. If compaction is needed, write to `memory/archives/YYYY-MM-DD-memory.md` first, then reduce.
4. Never use placeholder text. Empty is better than "(to be populated)" — the latter gets misread as "this file is empty, let me start fresh".

## Facts

_(Append facts about the repo, infra, decisions, constraints.)_

- 2026-04-30: `/Users/davidproctor/Documents/GitHub/entropy` was initialized as a git repository on branch `main`.
- 2026-04-30: GitHub repo `dp-pcs/entropy` exists, is private, and uses `origin` over SSH at `git@github.com:dp-pcs/entropy.git`.

## Decisions

_(Decisions made + one-line reason. Dated.)_

- 2026-04-30: Used repo name `entropy` under the authenticated GitHub owner `dp-pcs`; it matches the local directory name and avoids needless renaming friction.

## People

_(Humans involved. Names, roles, preferences if stated.)_

## Context

_(Anything that doesn't fit above but future-you will thank present-you for.)_

- 2026-04-30: Initial repository bootstrap was pushed to `origin/main` from commit `22cc40f`, then the bead ledger was updated locally to reflect the completed setup steps.
- 2026-05-12: Google credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) live in `.env` at repo root. The `webapp/oauth.py` file handles all OAuth flows. SYNAPSE_TOKEN also in `.env`.
- 2026-05-12: `webapp/session.py` uses an in-memory dict `_store` — sessions die on server restart. B0036 tracks migration to DynamoDB-backed store.
- 2026-05-12: DynamoDB table `entropy-users` (configurable via DYNAMODB_TABLE env var) stores google_sub → email, name, latest_job_id, jobs[]. Used by returning-user flow.
- 2026-05-12: Production BASE_URL is `https://entropy.elelem.expert`. AWS account: `913524910742` (prod-aicoe-admin via saml2aws). S3 bucket: `entropy-jobs-913524910742` (us-east-1). DynamoDB tables: `entropy-users` (user identity + job refs), `entropy-sessions` (session data + auth tokens, 24h/30d TTL). Use `saml2aws login -a prod-aicoe-admin --skip-prompt` before any prod AWS operations.

---

_Initialized empty intentionally. Do not add "(to be populated)" text._

- 2026-05-14: Local `bd-lite`/`memory/BEADS.md` task tracking is retired for this repo. Use central Beads hub at `~/.beads` with project metadata `entropy_builder`; see `~/.beads/INTEGRATION.md`.
- 2026-05-14: Synapse live contract addendum appended to `.agent/SYNAPSE.md`; briefs and `$SYNAPSE_URL/docs` supersede repo-local instructions. Current requirements include artifact-first evidence, `non_obvious_marker` for medium/high learnings, `supporting_learning_ids` for insights, `decision.record`, `question.*`, objective updates, feedback SLA, and Mission Control billing tags.
