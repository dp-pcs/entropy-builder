# Entropy

**Build a Second Brain that actually works — AI-assisted, personalized to how you think.**

Entropy is an open-source toolkit that scaffolds a personal knowledge system in Obsidian. Clone the repo, answer a few questions about your role and how you work, and walk away with a structured Second Brain built for you — frameworks, maps of content, and an AI-powered inbox processor that routes new information automatically.

---

## How it works

```
Clone repo → Open in Claude Code → Answer ~9 questions → Your brain is built
                                                               ↓
                                        Drop things in inbox → Plugin proposes where they go → Accept → Brain grows
```

1. **Clone** this repo and open it in [Claude Code](https://claude.ai/code)
2. **The agent detects** whether you're starting fresh or have existing notes (Workflowy, Notion, other markdown)
3. **Answer 9 questions** about your role, how you make decisions, your topic areas, and your operating boundaries — numbered options, no essays
4. **Your vault is built** — a Profile, role-specific frameworks, Maps of Content, and a navigation index, all scaffolded automatically
5. **Maintain it** — drop articles, clippings, or notes into your inbox. The Obsidian plugin analyzes them and proposes exactly where they belong. Accept with one click.

---

## Prerequisites

- [Obsidian](https://obsidian.md/) (free)
- [Claude Code](https://claude.ai/code) with an Anthropic account
- Python 3.8+

---

## Quick start

```bash
git clone https://github.com/dp-pcs/entropy
cd entropy
claude
```

Claude Code reads the repo, detects you're a new user, and launches the onboarding interview automatically. No configuration needed.

---

## What gets built

After the interview, Entropy creates your vault structure:

| File | What it is |
|------|-----------|
| `[YourName]-Profile.md` | Your operating style, POVs, strengths, and growth edges |
| `CLAUDE.md` | Your decision authority and operating boundaries |
| `frameworks/` | Role-specific frameworks (pre-seeded from your answers) |
| `mocs/` | Maps of Content for each of your topic areas |
| `TRAVERSAL-INDEX.md` | Your navigation layer — the map of everything |

---

## Starting point detection

Entropy meets you where you are. At the start of onboarding, it asks:

```
1. Fresh start — nothing organized yet
2. Workflowy — I can export my notes or BrainLifts
3. Notion — I have pages I can export
4. Other markdown files — .md or structured notes somewhere
5. Different Obsidian vault — I use Obsidian but differently organized
```

If you have existing content, it analyzes it first and only asks the questions it can't answer from what's already there.

---

## Inbox processing

Once your brain is built, the **Entropy Inbox Processor** Obsidian plugin keeps it growing.

**Keyword mode** (free): pattern-matches items against your existing structure  
**AI mode** (requires API key): semantic analysis — understands topics even without exact keyword matches

```bash
# Or run from the command line
python3 .agent/skills/process-inbox/analyzer.py ~/your-vault
# Review proposals.md, then:
python3 .agent/skills/process-inbox/apply.py ~/your-vault
```

**Supported import formats:**
- Web clippings (via Obsidian Clipper)
- Workflowy / BrainLift exports
- Notion markdown exports
- Any `.md` files

---

## Repo structure

```
entropy/
├── .agent/
│   ├── skills/
│   │   ├── onboard/           # First-run interview skill
│   │   └── process-inbox/     # Inbox analysis engine (Python)
│   └── ...                    # Agent operating context (SOUL, AGENT, MEMORY, BEADS)
├── obsidian-inbox-processor/  # Obsidian plugin (TypeScript)
├── input/                     # Onboarding documentation and role templates
├── AGENTS.md                  # Agent entry point (read first)
└── CLAUDE.md                  # Claude Code entry point (read first)
```

---

## Obsidian plugin setup

After onboarding, install the plugin into your vault:

```bash
VAULT=~/path/to/your-vault
mkdir -p "$VAULT/.obsidian/plugins/entropy-inbox-processor"
cp obsidian-inbox-processor/main.js \
   obsidian-inbox-processor/manifest.json \
   obsidian-inbox-processor/styles.css \
   "$VAULT/.obsidian/plugins/entropy-inbox-processor/"

# Link the Python backend
mkdir -p "$VAULT/.agent/skills"
ln -s "$(pwd)/.agent/skills/process-inbox" "$VAULT/.agent/skills/process-inbox"
```

Then in Obsidian: **Settings → Community plugins → Reload → Enable Entropy Inbox Processor**

---

## Built with

- [Obsidian](https://obsidian.md/) — the knowledge base
- [Claude Code](https://claude.ai/code) — the onboarding and maintenance agent
- Python 3 — inbox analysis engine
- TypeScript — Obsidian plugin

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built at [Trilogy](https://trilogy.com). Designed for people who think for a living.*
