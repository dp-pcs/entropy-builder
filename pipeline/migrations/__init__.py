"""Migration core, shared by the sync bot (scripts/sync_from_entropy.py) and
the vault-side migration applier (pipeline/migrations/applier.py).

One implementation of CHANGES parsing, validation, path/hash utilities, and
classifier methods. Two call sites: template-side (bot, via `handlers.py`)
and vault-side (applier, via `applier.py` — conflict-aware).
"""

