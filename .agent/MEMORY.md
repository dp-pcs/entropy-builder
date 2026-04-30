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

---

_Initialized empty intentionally. Do not add "(to be populated)" text._
