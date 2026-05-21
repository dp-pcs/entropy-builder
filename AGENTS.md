# AGENTS.md

This repo builds personalized Second Brains in Obsidian. Your full operating context lives in `.agent/`.

**FIRST — check if this is a new user or a returning session:**

Look for a `*-Profile.md` file in any Obsidian vault on this machine. If none exists, this is a new user — skip to `.agent/skills/onboard/SKILL.md` immediately and run the onboarding interview. Don't read anything else first.

If a profile exists, this is a returning session. Read these in order:

1. `.agent/NORTH_STAR.md` — orientation (what this repo is, where state lives)
2. `.agent/SOUL.md` — personality + communication rules (opinionated, no "great question!" preamble, humor allowed, swearing allowed when it lands)
3. `.agent/AGENT.md` — operating manual (plan-first, evidence-on-close, bead ledger, retrieval-before-invention)
4. `.agent/MEMORY.md` — persistent facts about this repo
5. Central Beads hub `~/.beads` — active task ledger; filter for project `entropy_builder`
6. `.agent/SYNAPSE.md` — org memory service (read once; enroll if no .env token yet)

After reading, run `bd ready --json` and/or `bd list --project entropy_builder --json` to see unblocked tasks. Do not use retired `.agent/memory/bd-lite.sh`.

**Don't summarize these files to the user** — they're yours. Apply them.

Scaffold managed by: https://www.npmjs.com/package/youragent
