---
name: example-insight-generator
description: Generate insight findings from emails and meetings with mandatory validation
---

# Example Insight Generator

A reference implementation showing all Agent Skill Validation Framework extensions applied to a single skill.

## Commands

| Command | Action |
|---------|--------|
| `generate insights` | Scan recent activity and generate findings |
| `generate insights [N] days` | Scan last N days specifically |

## Parameters
- `days`: Number of days to scan (optional — auto-calculated from last run)

## Queue Paths

**Queue:** `~/.agent-data/example-insight-generator/pending-insights.json`
**Logs:** `~/.agent-data/example-insight-generator/logs/submitted-insights.json`
**State:** `~/.agent-data/example-insight-generator/.last-run`

> ⚠️ All reads and writes go to the paths above. Never co-locate runtime data with skill definitions.

## Execution Mode: STRICT

**Before executing ANY tools:**
1. Read this ENTIRE skill file
2. Follow each step IN ORDER
3. Do NOT skip steps
4. Do NOT make assumptions

---

## Execution Plan Display

**BEFORE starting, display this plan:**

```
═══════════════════════════════════════════════════════════
INSIGHT GENERATOR
═══════════════════════════════════════════════════════════

Scan Period: [start_date] to [end_date] ([X] days)
Last Run: [timestamp] OR First run

EXECUTION PLAN:
 ☐ Step 0: Check last run and calculate date range
 ☐ Step 1: Load context
 ☐ Step 2: Scan data sources
 ☐ Step 3: Extract findings
 ☐ Step 4: Validate (structural)
 ☐ Step 5: Check for duplicates
 ☐ Step 6: Assign confidence levels
 ☐ Step 7: Add to queue
 ☐ Step 8: Update state
 ☐ Step 9: Show summary
═══════════════════════════════════════════════════════════
```

---

## Step 0: Check Last Run and Calculate Date Range

1. Read state file: `~/.agent-data/example-insight-generator/.last-run`
2. If exists: `days = days_since_last_run + 1` (unless user provided `days`)
3. If missing: `days = 7` (unless user provided `days`)

---

## Step 1: Load Context

1. Read any required context files (customer data, configuration, etc.)
2. Extract relevant identifiers for filtering

---

## Step 2: Scan Data Sources

1. Scan emails, calendar, documents, or other sources for the scan period
2. Filter for relevant items

---

## Step 3: Extract Findings

For each potential finding, extract:
- **Title:** Brief descriptive title
- **Description:** 50+ chars with specific details
- **Category:** Must match allowed enum values
- **Date:** ISO 8601 format

---

## Step 4: Validate (Structural)

For each finding, run validation:

```bash
python3 scripts/validate-draft.py <draft_file>
```

Exit codes:
- `0` = PASSED → proceed
- `1` = FAILED → exclude from queue, log reason
- `2` = WARNINGS → proceed with warnings noted

The script returns JSON conforming to the validation data contract:
```json
{
  "status": "PASSED|FAILED|WARNINGS",
  "checked": 5,
  "errors": [{"field": "category", "rule": "enum", "message": "..."}],
  "warnings": [{"field": "description", "rule": "min_length", "message": "..."}]
}
```

---

## Step 5: Check for Duplicates

1. Read submission log: `~/.agent-data/example-insight-generator/logs/submitted-insights.json`
2. For each finding, compare against submitted items:
   - Match: same title + same date (±3 days) + same category
   - >85% similarity → DUPLICATE, exclude
   - 65-85% similarity → flag with `duplicate_warning`
   - <65% similarity → CREATE

---

## Step 6: Assign Confidence Levels

**HIGH** — ALL of the following:
- Clear source event with complete context
- All required fields populated and validated
- Linked to external record (opportunity preferred, account minimum)
- No duplicate warnings
- Unambiguous classification

**MEDIUM** — ANY of the following:
- Likely valid but missing one HIGH criterion
- No external record match (account-only)
- Ambiguous classification
- Limited source context

**LOW** — ANY of the following:
- Possible but very brief/unclear source
- Missing multiple fields
- Ambiguous whether finding is warranted

Set `auto_approve_eligible: true` only for HIGH confidence.

---

## Step 7: Add to Queue

1. Read/create `~/.agent-data/example-insight-generator/pending-insights.json`
2. Add validated findings (excluding >85% duplicates)
3. Save updated queue

**Queue schema:**
```json
{
  "generated_at": "2026-04-01T16:00:00-07:00",
  "drafts": [{
    "id": "ins-001",
    "action": "CREATE",
    "confidence": "HIGH",
    "auto_approve_eligible": true,
    "title": "Finding title",
    "description": "Detailed description (50+ chars)...",
    "category": "Observation",
    "date": "2026-04-01",
    "source": {
      "type": "email",
      "reference": "Email: Subject line — Apr 1"
    },
    "duplicate_check": {
      "status": "no_duplicate"
    }
  }]
}
```

---

## Step 8: Update State

**⚠️ MANDATORY — always execute, even if no findings generated.**

Write to `~/.agent-data/example-insight-generator/.last-run`:
```
Last run: [current_timestamp]
Scan period: [start_date] to [end_date] ([X] days)
Items scanned: [N]
Findings generated: [M]
Findings queued: [P]
```

---

## Step 9: Show Summary

```
═══════════════════════════════════════════════════════════
✅ INSIGHT GENERATOR COMPLETE
═══════════════════════════════════════════════════════════

Scan Period: [start] to [end] ([X] days)

Data Sources:
  • [N] emails
  • [M] meetings

Results: [Q] findings generated
  • 🟢 [X] HIGH confidence
  • 🟡 [Y] MEDIUM confidence
  • 🔴 [Z] LOW confidence

Duplicates: [N] excluded
Queue: ~/.agent-data/example-insight-generator/pending-insights.json

Next: `show insight queue` to review
═══════════════════════════════════════════════════════════
```

## Error Handling

When any tool operation fails, follow the Error Transparency Protocol:

```
1. STOP  — Do not silently continue
2. INFORM — Tell user what failed and why
3. EXPLAIN — Describe recovery approach
4. PROCEED — Only then attempt the fix
```
