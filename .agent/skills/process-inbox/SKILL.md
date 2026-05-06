---
name: process-inbox
description: Analyze inbox/raw items and propose integration into second brain structure
trigger: "process inbox|process clippings|integrate raw"
version: 0.1.0
author: entropy
---

# process-inbox

Analyzes unprocessed items in a second brain's inbox or clippings folder and proposes specific integration actions (update framework, create wikilink, add to knowledge base, etc.)

## Setup (First Time Only)

```bash
# Create necessary directories and get clipper setup instructions
python3 .agent/skills/process-inbox/setup-inbox.py ~/your-vault

# Creates:
# - 00-Inbox/, Clippings/, raw/, raw/assets/, raw/processed/
# - frameworks/, mocs/, knowledge/, sources/, people/
# - raw/.gitignore, raw/README.md
# - Prints Obsidian clipper configuration instructions
```

## Usage

**Two workflows depending on what you're importing:**

### Workflow 1: Regular Items (articles, clippings, notes)

```bash
# Step 1: Analyze inbox → generates proposals.md

# Option A: Fast keyword matching (free, no API key needed)
python3 .agent/skills/process-inbox/analyzer.py ~/your-vault

# Option B: AI-powered semantic analysis (better accuracy, costs ~$0.20/50 items)
python3 .agent/skills/process-inbox/analyzer.py ~/your-vault \
  --use-ai \
  --provider anthropic \
  --api-key sk-ant-...

# Or with OpenAI
python3 .agent/skills/process-inbox/analyzer.py ~/your-vault \
  --use-ai \
  --provider openai \
  --api-key sk-...

# Step 2: Review proposals.md → mark ACCEPT/REJECT/EDIT

# Step 3: Apply approved changes → archives to raw/processed/
python3 .agent/skills/process-inbox/apply.py ~/your-vault
```

**AI Analysis Features:**
- ✨ **Semantic understanding** - Understands topics even without exact keywords
- 🎯 **Better relationship detection** - Finds connections you'd miss with keywords
- 💡 **Smarter insights** - Extracts actual key points, not just first paragraph
- 🏷️ **Topic naming** - Better MOC suggestions from content analysis

**Cost estimates:**
- Claude Sonnet 3.5: ~$0.003/item (~$0.15 for 50 articles)
- GPT-4o: ~$0.004/item (~$0.20 for 50 articles)
- GPT-4o-mini: ~$0.0006/item (~$0.03 for 50 articles)

### Workflow 2: BrainLift Items (structured research from Workflowy)

```bash
# Step 1: Split Workflowy export into individual BrainLifts
python3 .agent/skills/process-inbox/split-brainlifts.py <export.md> --output-dir ~/your-vault/00-Inbox

# Step 2: Preview categorization
python3 .agent/skills/process-inbox/process-brainlifts.py ~/your-vault --preview

# Step 3: Process BrainLifts → creates sources/frameworks, moves to knowledge/
python3 .agent/skills/process-inbox/process-brainlifts.py ~/your-vault
```

**How to know which workflow to use:**
- Regular items: Articles, blog posts, notes, PDFs, single-topic content → Use Workflow 1
- BrainLifts: Multi-section research with DOK levels, SPOVs, Experts → Use Workflow 2

## What it does

**Workflow 1 (Regular Items):**
1. **Scans** inbox folders (00-Inbox/, Clippings/, raw/)
2. **Analyzes** each item against existing brain structure
3. **Detects topic clusters** - If 3+ unrelated items share a topic, suggests creating MOC
4. **Proposes** specific integration actions with diff previews
5. **Generates** proposals.md for user review
6. **Applies** approved changes after user edits proposals
7. **Archives** reviewed items to raw/processed/

**Automatic MOC Suggestions:**
- If you drop 5 articles about "RAG Architecture" and have no RAG MOC, the system will:
  - Detect the cluster of related items
  - Suggest creating "RAG Architecture MOC"
  - Show which items would be linked
  - Let you accept/reject the suggestion
- This aligns with Karpathy's principle: **LLM maintains structure, you just add content**

**Workflow 2 (BrainLifts):**
1. **Splits** Workflowy export into individual BrainLift files
2. **Categorizes** as sources (your research) / frameworks (your methodologies) / knowledge (reference)
3. **Extracts** SPOVs, insights, experts from DOK structure
4. **Creates** distilled files in sources/ and frameworks/
5. **Preserves** full BrainLifts in knowledge/ for reference
6. **Lists** SPOVs and experts for profile/people/ integration

## Capturing Content (Obsidian Clipper Setup)

To capture web articles with images preserved:

1. **Install Web Clipper plugin** in Obsidian
   - Settings → Community Plugins → Browse → "Web Clipper"

2. **Configure clipper settings:**
   - Save location: `Clippings/`
   - Download images: **ON**
   - Image save location: `raw/assets/`
   - Add frontmatter: **ON**

3. **Why this works (Karpathy pattern):**
   - Markdown files reference: `![](raw/assets/image-name.jpg)`
   - When file moves to knowledge/, relative path stays valid
   - Assets stay in one place, wikilinks don't break
   - Can `.gitignore` assets/ to keep repo small

**Example frontmatter template:**
```yaml
---
type: clipping
source: {{url}}
author: {{author}}
date_clipped: {{date}}
---
```

## Proposal Format

### MOC Suggestions (if clusters detected)

If the analyzer finds 3+ unrelated items sharing a topic:

```markdown
## 🎯 Suggested New MOCs

### MOC Suggestion: RAG Architecture
**Items in cluster:** 4
**Detected topic:** rag

**Items:**
- RAG Architecture Patterns.md
- Vector Database Comparison.md
- RAG vs Fine-tuning.md
- Embedding Models for RAG.md

### ACTION: CREATE MOC
**Target:** `mocs/RAG-Architecture-MOC.md`
**Rationale:** 4 items about 'rag' suggest new navigation hub

[ACCEPT] [REJECT]
```

### Individual Item Proposals

Each item gets analyzed and you see:

```markdown
## Item: "Article Title.md"

**Analysis:**
- Relates to: [[Existing-Framework]]
- Confidence: 85%
- Key insight: [One sentence summary]

**Proposed Actions:**

### ACTION 1: Update existing framework
File: frameworks/Existing-Framework.md
Add to "Real World Examples" section:
```diff
+ New example from article with citation
```
[ACCEPT] [REJECT] [EDIT]

### ACTION 2: Create wikilink
In frameworks/Existing-Framework.md, add:
`See [[Article Title]] for counter-example.`
[ACCEPT] [REJECT]

### ACTION 3: Add to knowledge base
Create knowledge/New-Topic.md
[ACCEPT] [SKIP]
```

## User Review Process

1. Agent generates `proposals.md`
2. You review and mark each action:
   - `[ACCEPT]` → do it
   - `[REJECT]` → skip it
   - `[EDIT]` → you modify the proposed text inline
3. Run `/process-inbox --apply` to execute approved changes
4. Agent updates TRAVERSAL-INDEX.md
5. Processed items move to raw/processed/

## Configuration

Place `.process-inbox.json` in vault root:

```json
{
  "inbox_folders": ["00-Inbox", "Clippings", "raw"],
  "confidence_threshold": 0.7,
  "auto_wikilink": true,
  "require_approval": true
}
```

## Agent Instructions

When you invoke this skill:

1. **Find the vault:** Look for second brain structure (TRAVERSAL-INDEX.md, frameworks/, mocs/, etc.)

2. **Scan inbox folders:** Read all .md files in inbox directories

3. **For each item:**
   - Read the full content
   - Read TRAVERSAL-INDEX.md to understand brain structure
   - Read related frameworks/MOCs/knowledge docs
   - Identify relationships with confidence scores
   - Generate specific, actionable proposals (not vague suggestions)
   - Show diffs for proposed changes

4. **Generate proposals.md** with:
   - Item-by-item analysis
   - Specific proposed actions (updates, wikilinks, new docs)
   - [ACCEPT] [REJECT] [EDIT] markers
   - Diff previews for all changes

5. **Wait for user review:** Don't auto-apply anything

6. **After user edits proposals.md:**
   - Parse approval markers
   - Apply ACCEPT changes
   - Use EDIT changes (user-modified text)
   - Skip REJECT changes
   - Update TRAVERSAL-INDEX.md
   - Move processed files to raw/processed/
   - Generate processing-summary.md with what was done

## Quality Checks

✅ **DO:**
- Propose specific edits with exact text
- Show confidence scores (0-100%)
- Link to existing content, don't duplicate
- Flag contradictions ("This says X but your framework says Y")
- Suggest deletion if item adds nothing new
- Respect existing voice and style

❌ **DON'T:**
- Auto-apply without approval
- Create new frameworks (user should do that intentionally)
- Overwrite existing content without diff
- Make vague suggestions ("this relates to X")
- Add content that contradicts existing frameworks without flagging

## Example Output

After processing 10 items:

```
Processing Summary — 2026-05-04

✅ Processed: 10 items
✅ Applied: 23 actions (18 accepted, 5 edited)
❌ Skipped: 7 actions (rejected)
📦 Archived: 10 items → raw/processed/2026-05-04/

Changes made:
- Updated 5 frameworks
- Added 12 wikilinks
- Created 2 knowledge docs
- Updated TRAVERSAL-INDEX.md

Next steps:
- 0 items remaining in inbox
- Brain is current as of 2026-05-04
```

## Integration with Obsidian Plugin

This skill is designed to work standalone OR be called by an Obsidian plugin. The plugin would:
- Show proposals in sidebar UI instead of markdown file
- Provide accept/reject buttons
- Live preview of changes
- But the CORE LOGIC stays in this skill

## BrainLift Processing

**BrainLifts** are structured research artifacts with DOK (Depth of Knowledge) levels:
- **DOK 4:** Spiky Points of View (SPOVs) - your strongest claims/principles
- **DOK 3:** Insights - key findings
- **DOK 2:** Knowledge Tree - categorized sources
- **DOK 1:** Facts - raw data
- **Experts:** People who influenced the research
- **Purpose:** What the research is about

### BrainLift Workflow

If you export BrainLifts from Workflowy or similar tools:

**Step 1: Split** (if exported as one file)
```bash
python3 split-brainlifts.py <workflowy-export.md> --output-dir brainlifts/
# Creates individual BrainLift-*.md files with frontmatter
```

**Step 2: Process**
```bash
python3 process-brainlifts.py ~/David-Proctor-Second-Brain --preview
# Shows categorization (sources/frameworks/knowledge)
# Shows SPOV count, expert count

python3 process-brainlifts.py ~/David-Proctor-Second-Brain
# Creates distilled files in sources/ and frameworks/
# Preserves full BrainLifts in knowledge/
```

### What BrainLift Processing Does

**Categorization Logic:**
- **Sources** → Your published research/papers (e.g., "GEPA", "Expertise Inflation")
- **Frameworks** → Methodologies you built (e.g., "OGP", "Multi-Tenant Gateway")
- **Knowledge** → Technology deep-dives and reference material

**For Sources:** Creates concise file with:
- Top 3 SPOVs (first paragraph each)
- Top 5 insight titles
- Key experts
- Link to full BrainLift

**For Frameworks:** Creates methodology doc with:
- All SPOVs as "Core Principles"
- All insights as "Application Guidance"
- Related experts
- Link to full BrainLift

**Extraction:**
- All SPOVs → Consider adding to profile
- All unique experts → Create people/ entries

## Notes

- Requires read access to entire vault
- Preserves YAML frontmatter
- Maintains wikilink integrity
- Updates TRAVERSAL-INDEX.md automatically
- Never deletes anything (moves to processed/)
- BrainLift originals preserved in knowledge/ folder
