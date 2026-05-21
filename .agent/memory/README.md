# Retired local task ledger

This directory no longer owns active task state.

Use the central Beads hub instead:

```bash
export BEADS_DIR=$HOME/.beads
bd ready --json
bd list --project entropy_builder --json
bd update <id> --claim
bd close <id> --reason "<specific evidence>"
```

See `~/.beads/INTEGRATION.md` for the hub contract.

Historical notes:
- `bd-lite.sh` and `BEADS.md` were retired on 2026-05-14.
- Archived copies, if still present, were moved to `/tmp/bd-lite-archive/entropy_builder/`.
- Older docs in this repo may mention `bd-lite`; translate those references to central `bd` commands against `~/.beads`.
