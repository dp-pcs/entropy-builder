# Analytics Reference Layer

Referenceable definitions, verified queries, and schemas that any Portfolio Brain skill can draw on. Separating these from skills means you can load just the metric definition without also loading the SQL, or just the query pattern without the full schema.

| File | What's Inside | When to Read |
|------|--------------|-------------|
| `metrics.md` | Health score formula, risk bands, sentiment scales, segment definitions, cancellation intent weights | When you need to know how a metric is defined or what a score means |
| `queries.md` | Fionn API calls, Jira JQL, Gmail search patterns, Notion database IDs, Read.ai patterns | When you need to pull data from an MCP source |
| `schemas.md` | Canonical YAML frontmatter for intelligence summaries, playbooks, outcomes, transcripts | When creating or validating file structures |
