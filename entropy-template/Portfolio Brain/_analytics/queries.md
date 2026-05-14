# Portfolio Brain Verified Query Patterns

Tested MCP tool calls and query patterns for pulling customer data. Use these instead of guessing parameter names or query syntax — they've been validated against real data.

## Fionn MCP

### Dashboard (full account snapshot)
```
Tool: fionn_get_dashboard
Args: { customer_name: "Exact Customer Name" }
Returns: ARR, AI signal, overdue balance, renewal date, days to renewal, contacts
```
**Note:** Dashboard output can be very large (2.4M+ chars for full portfolio). When querying a specific customer, grep the output for the customer name rather than reading the full response.

### Financial Data
```
Tool: fionn_get_financial_data
Args: { customer_name: "Exact Customer Name" }
Returns: Contract details, invoices, payment history, ARR breakdown
```

### Email History
```
Tool: fionn_get_email_history
Args: { customer_name: "Exact Customer Name" }
Returns: Recent email threads tracked in Fionn
```

### Notes
```
Tool: fionn_get_notes
Args: { customer_name: "Exact Customer Name" }
Returns: Internal notes logged against the account
```

### Overdue Balance
```
Tool: fionn_get_overdue_balance
Args: { customer_name: "Exact Customer Name" }
Returns: Outstanding invoices and amounts
```

### AR Info
```
Tool: fionn_get_ar_info
Args: { customer_name: "Exact Customer Name" }
Returns: Accounts receivable details
```

---

## Gmail MCP

### Search for customer emails
```
Tool: search_threads
Args: { query: "from:@customerdomain.com newer_than:30d" }
Returns: Thread IDs, subjects, participants, dates
```

### Search by contact name
```
Tool: search_threads
Args: { query: "from:contact.name@domain.com newer_than:30d" }
```

### Read a specific thread
```
Tool: get_thread
Args: { thread_id: "thread_id_from_search" }
Returns: Full thread content
```

**Patterns for daily scan:**
- `newer_than:1d` — last 24 hours
- `newer_than:2d` — weekend catch-up (Saturday + Sunday)
- `newer_than:7d` — weekly review

---

## Jira MCP

### Search tickets by customer domain
```
Tool: searchJiraIssuesUsingJql
Args: { 
  jql: "reporter in membersOf('customer-group') AND updated >= -7d ORDER BY updated DESC",
  cloudId: "<cloud-id>"
}
```
**Known issue:** Cloud ID lookup for `trilogy-group.atlassian.net` can return 404. Fallback: use ticket data already catalogued in intelligence summaries (Jira/ folder).

### Search by ticket key
```
Tool: getJiraIssue
Args: { issueKey: "PROJ-123", cloudId: "<cloud-id>" }
```

### Find critical/blocker tickets
```
JQL: "priority in (Critical, Blocker) AND status != Done AND updated >= -7d"
```

---

## Read.ai MCP

### List recent meetings
```
Tool: list_meetings
Args: {} (returns recent meetings)
```

### Get meeting details
```
Tool: get_meeting_by_id
Args: { meeting_id: "meeting_id_from_list" }
Returns: Transcript, summary, action items, participants
```

---

## Notion MCP

### Query customer database
```
Tool: notion-query-data-sources
Database ID: 28485e927d3181c89d6cdd6fd57ea07d
```
Returns: Customer names, ARR, renewal dates, status, contacts, success level

**Sync cadence:** Monthly ONLY (1st of month). Not daily, not weekly.

---

## Kayako MCP

### Search support tickets
```
Tool: search_tickets
Args: { query: "customer name or domain" }
Returns: Ticket IDs, subjects, status, priority, assignee
```

---

## Google Drive MCP

### Search for customer files
```
Tool: search_files
Args: { query: "Customer Name" }
```

### Upload a file (e.g., CS deck)
```
Tool: create_file
Args: {
  title: "Document Title",
  base64Content: "<base64-encoded-content>",
  contentMimeType: "application/vnd.openxmlformats-officedocument.presentationml.presentation"
}
```
Google Drive auto-converts PPTX → Google Slides, XLSX → Google Sheets, DOCX → Google Docs.

---

## Domain Mapping

**File:** `Portfolio Brain/_data/customer_domains.json`
**446 domains** mapped to customer names and products.

**Reseller domains (multi-customer):**
- shi.com
- carahsoft.com
- penril.net
- softwareone.com
- bechtle.com
- tekservinc.com

For reseller domains, disambiguate using email subject/body content, not just the domain.

**Regeneration:** During monthly enrichment from Notion database.
