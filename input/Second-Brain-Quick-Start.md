# Second Brain Quick Start
**1-Page Cheat Sheet**

---

## In 60 Seconds

A **Second Brain** is a personal knowledge system that:
- Makes *you* smarter (decision support, faster thinking)
- Makes your team smarter (shared frameworks, collective intelligence)
- Makes AI agents useful (bounded, trustworthy context)

Built in Obsidian. Based on Karpathy's knowledge graph model. Follows 4 rules:
1. **Identity**: Know who you are (profile + operating principles)
2. **Knowledge**: Curate what you know (frameworks, sources, expertise)
3. **Navigation**: Connect the dots (wikilinks, MOCs)
4. **Share selectively**: Contribute to organizational intelligence

---

## What You Need (Must-Haves)

✅ **Your Profile** (`[Name]-Profile.md`)
- Operating style, spiky POVs, strengths, growth edges

✅ **Operating Rules** (`CLAUDE.md`)
- Approval matrices, boundaries, company constraints

✅ **3–5 Frameworks** (`frameworks/` folder)
- Your actual operating systems (not generic theory)

✅ **5–10 Sources** (`sources/` folder)
- Books, courses, mentors who shaped your thinking

✅ **2–3 MOCs** (`mocs/` folder)
- Maps of Content (navigation clusters for your domain)

✅ **Knowledge Base** (`knowledge/` folder)
- Product docs, policies, domain expertise

✅ **TRAVERSAL-INDEX** (`TRAVERSAL-INDEX.md`)
- Master file listing (so you can find things)

**Time to build baseline:** 6–15 hours (or 7 days at 2 hours/day)

---

## Phases (7-Day Plan)

| Day | What | Time | Output |
|-----|------|------|--------|
| **Day 1** | Profile + Rules + Index skeleton | 2h | Identity established |
| **Day 2** | Knowledge base (product docs, policies) | 2–3h | Knowledge articles created |
| **Day 3** | Frameworks (3–5 of them) | 2–3h | Operational expertise documented |
| **Day 4** | Sources + People | 1.5h | Influences recorded |
| **Day 5** | MOCs (2–3 of them) | 1h | Navigation structure built |
| **Day 6** | Wikilinks + Update Index | 1h | Brain is connected |
| **Day 7** | Role-specific enhancements | 2–4h | Personalization complete |
| **Total** | | 12–15h | Functional, shareable brain |

---

## Framework Template (Copy This)

```markdown
---
type: framework
name: "[Framework Name]"
role: "[Your Role]"
description: "[One-liner]"
when_to_use: "[When you apply this]"
tags: ["tag1", "tag2"]
is_shareable: true
last_updated: 2026-04-23
---

# [Framework Name]

## Why This Works
[2–3 sentences on logic]

## The Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Real Example
[From your actual work]

## Common Mistakes
- [Mistake 1]

## When It Breaks
[Limitations]

## Related
- [[Other Framework]]
- [[Source Book]]
```

---

## Your Brain's Structure

```
[Your Name]'s Second Brain/
├── CLAUDE.md                  ← Rules & boundaries
├── TRAVERSAL-INDEX.md         ← Master file list
├── [YourName]-Profile.md      ← Who you are
├── knowledge/                 ← Product docs, policies
│   ├── [Product]/
│   ├── Company Policies/
│   └── Industry Intelligence/
├── frameworks/                ← Your operating systems (3–5)
│   ├── Framework 1.md
│   ├── Framework 2.md
│   └── [...]
├── sources/                   ← Curated (5–10)
│   ├── Book 1.md
│   └── [...]
├── people/                    ← Mentors (3–5)
├── mocs/                      ← Navigation (2–3)
│   ├── MOC 1.md
│   └── MOC 2.md
├── cases/                     ← [Optional] Win/loss examples
├── personas/                  ← [Optional] Buyer types
└── raw/                       ← Unprocessed intake
```

---

## Metadata (Every File Needs This)

```yaml
---
type: "profile" | "rule" | "documentation" | "framework" | "source" | "person" | "moc"
name: "Human-readable name"
description: "One-line summary"
role: "Sales" | "Product" | "Marketing" | [optional]
tags: ["tag1", "tag2", "tag3"]
is_shareable: true | false
last_updated: "2026-04-23"
---
```

---

## Role-Specific Must-Haves

**Sales**: Enterprise Sales Process, Account Planning, Negotiation, Renewal, Expansion

**Product**: Feature Prioritization, Roadmap Planning, User Research, Technical Debt, Metrics

**Marketing**: Campaign Planning, Content Strategy, Buyer Personas, Attribution

**Any Role**: Decision-Making Framework, Learning MOC, Operational MOC

---

## Wikilinks (How Brain Connects)

```markdown
- Framework links to Source: [[Never Split the Difference]]
- MOC links to Framework: [[Account Planning Framework]]
- Framework links to MOC: [[Enterprise Sales MOC]]
```

**Rule**: 2–5 links per file (not every file links to every file)

---

## Validation Checklist

Before considering your brain "done":

- [ ] All files have YAML frontmatter
- [ ] Every file has 2+ wikilinks (except MOCs)
- [ ] MOCs are navigable (you can find related concepts in <2 clicks)
- [ ] TRAVERSAL-INDEX lists all files with descriptions
- [ ] You can answer a work question using your brain (not Google)
- [ ] No files >6 months old (or marked as stale)
- [ ] is_shareable set correctly (true/false in every file)

---

## What Success Looks Like

**Week 1**: Brain exists. Rough. Missing connections.

**Week 2**: Brain is connected. You consult it for decisions.

**Week 3**: Brain is refined. Peer asks to see a framework.

**Month 1**: Brain is habit. You use it daily. Team notices (faster decisions, better context).

**Month 3**: Team has multiple brains. Federation tests start. Cross-functional queries work.

**Month 6**: Org-wide Second Brains. New hires onboard with access to collective knowledge.

---

## Maintenance (Keep It Alive)

**Weekly** (5 min):
- Open brain, review one MOC or framework
- Ask: "Does this still match how I work?"

**Monthly** (30 min):
- Review TRAVERSAL-INDEX
- Mark stale files
- Add 1 case study or update 1 framework

**Quarterly** (1 hour):
- Full audit (frontmatter consistency, broken links)
- Update profile if anything changed (new POV? new growth edge?)
- Delete irrelevant files

---

## Common Mistakes (Don't Do These)

❌ Brain bloat (500+ nodes, mostly junk)
→ Curate ruthlessly. If you won't reread it, don't add it.

❌ No connections (isolated notes)
→ After adding file, add 3–5 wikilinks to related concepts.

❌ Frameworks are generic theory
→ Document how *you* actually work, not how textbooks say you should.

❌ Too many MOCs
→ Start with 2–3. Add more later if needed. Fewer > more.

❌ Not using it
→ Query your brain once before deciding. Notice: faster? Better aligned? If yes, keep going.

---

## Next Steps

1. **Read** [[Second-Brain-Template-Framework.md]] (30 min)
2. **Do** Phase 0 interview (45 min) from [[Second-Brain-Onboarding-Checklist.md]]
3. **Build** Phases 1–3 (6–8 hours across 5 days)
4. **Review** daily; adjust as needed
5. **Share** selectable frameworks with peers (when ready)

---

## Tools You Need

- **Obsidian** (free) — the app
- **Google Drive** (free) — for syncing across devices (optional but recommended)
- **15–20 minutes per day** — to build steadily without burnout

---

## Questions?

- **How do I get started?** → Follow the 7-day plan above
- **Can I customize the frameworks?** → YES. The examples are scaffolds, not rules.
- **Will my brain become stale?** → Only if you stop maintaining it. Quarterly refresh keeps it fresh.
- **Can people steal my personal notes?** → No. Mark as `is_shareable: false`. Only shareable content enters org hub.
- **What if I'm not organized?** → This system *makes* you organized. Start anyway.

---

## Final Reminder

Your Second Brain works best as a **living tool, not a static archive**.

- Use it to make decisions (not just to store knowledge)
- Update it weekly (5 min)
- Share selectively (frameworks, not secrets)
- Iterate constantly (it evolves as you evolve)

In 2 weeks, you'll have a brain. In 2 months, you'll use it daily. In 6 months, it'll be irreplaceable.

---

**Let's build.**

---

**See also:**
- [[Second-Brain-Template-Framework.md]] — Full spec
- [[Second-Brain-Onboarding-Checklist.md]] — Detailed walkthrough
- [[Role-Specific-Brain-Baselines.md]] — Examples for your role
- [[README-Second-Brain-System.md]] — System overview
