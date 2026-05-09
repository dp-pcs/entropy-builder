# CLAUDE.md

This repo uses the `youragent` scaffold. Your full operating context lives in `.agent/`.

**On every session, read these in order:**

1. `.agent/NORTH_STAR.md` — orientation (what this repo is, where state lives)
2. `.agent/SOUL.md` — personality + communication rules (opinionated, no "great question!" preamble, humor allowed, swearing allowed when it lands)
3. `.agent/AGENT.md` — operating manual (plan-first, evidence-on-close, bead ledger, retrieval-before-invention)
4. `.agent/MEMORY.md` — persistent facts about this repo
5. `.agent/memory/BEADS.md` — active task ledger
6. `.agent/SYNAPSE.md` — org memory service (read once; enroll if no .env token yet)

After reading, run `./.agent/memory/bd-lite.sh ready` to see unblocked tasks.

**Don't summarize these files to the user** — they're yours. Apply them.

Scaffold managed by: https://www.npmjs.com/package/youragent
