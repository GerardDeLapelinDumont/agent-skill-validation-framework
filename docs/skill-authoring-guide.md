# Skill Authoring Guide: SOP/Validated/Strict Framework

**Version:** 1.1
**Author:** Gerard De Lapelin Dumont
**Date:** April 22, 2026
**Status:** Released

## Overview

This guide codifies our skill authoring patterns into a reusable framework. It extends the [Anthropic Agent Skills Open Standard](https://agentskills.io) with three execution enforcement layers designed for deterministic, auditable AI agent behavior.

Our extensions address gaps the Anthropic standard explicitly acknowledges as unsolved: opaque skill triggering, no cross-session state, and no validation protocol.

---

## Compatibility

| Layer | Anthropic Standard | Our Extension |
|-------|-------------------|---------------|
| Directory structure (`SKILL.md`, `scripts/`, resources) | ✅ Native | — |
| YAML frontmatter (name, description) | ✅ Native | — |
| Progressive disclosure (metadata → instructions → resources) | ✅ Native | — |
| Executable scripts with JSON output | ✅ Native | — |
| **Execution Mode: STRICT** | ❌ Not defined | ✅ Our extension |
| **Execution Plan Display** | ❌ Not defined | ✅ Our extension |
| **Confidence-gated validation** | ❌ Not defined | ✅ Our extension |
| **Validation scripts with exit codes** | ❌ Not defined | ✅ Our extension |
| **Cross-session state persistence** | ❌ Acknowledged gap | ✅ Our extension |
| **Error transparency protocol** | ❌ Not defined | ✅ Our extension |

---

## 1. Skill Structure (Anthropic-Compatible)

```
my-skill/
├── SKILL.md              # Core instructions + YAML metadata
├── README.md             # Human-readable description
├── CHANGELOG.md          # Version history
├── scripts/              # Executable validation/automation
│   └── validate-draft.py
└── references/           # Supporting docs loaded on-demand
    └── rubrics.md
```

### SKILL.md Frontmatter (Required)

```yaml
---
name: my-skill-name
description: One-line description used for skill triggering and discovery
---
```

The `description` field determines when the agent loads the skill. Be specific: "Generate SA activity queue from emails/meetings with mandatory validation" triggers reliably. "Helps with activities" does not.

---

## 2. Execution Mode: STRICT

Every skill that performs multi-step operations MUST declare STRICT execution mode.

### Declaration

Place this immediately after the Commands table:

```markdown
## Execution Mode: STRICT

**Before executing ANY tools:**
1. Read this ENTIRE skill file
2. Follow each step IN ORDER
3. Do NOT skip steps
4. Do NOT make assumptions
```

### Why This Exists

LLMs are non-deterministic by nature. Without STRICT mode, the agent may:
- Skip steps it considers "unnecessary"
- Reorder steps based on its own reasoning
- Make assumptions instead of reading data
- Silently recover from errors without informing the user

STRICT mode forces sequential, auditable execution — the closest we can get to deterministic behavior from a probabilistic system.

---

## 3. Execution Plan Display

Before ANY tool calls, the skill MUST display a numbered checkbox plan to the user.

### Template

```markdown
## Execution Plan Display

**BEFORE starting, display this plan:**

═══════════════════════════════════════════════════════════
[SKILL NAME IN CAPS]
═══════════════════════════════════════════════════════════

Context: [relevant parameters]

EXECUTION PLAN:
 ☐ Step 0: [Pre-flight check — state, date range, etc.]
 ☐ Step 1: [First data gathering step]
 ☐ Step 2: [Second data gathering step]
 ...
 ☐ Step N-2: [Validation]
 ☐ Step N-1: [Output/queue/save]
 ☐ Step N: [Update state + show summary]
```

### Rules

- Display the plan BEFORE executing any steps
- Each step maps 1:1 to a `## Step N:` section in the SKILL.md
- The plan acts as a contract — the agent commits to executing all steps
- Users can see progress and catch skipped steps

---

## 4. Validation Framework (3-Tier)

Every skill that generates output for external systems (SFDC, email, files) MUST implement validation.

### Tier 1: Structural Validation

Check that required fields exist and conform to expected formats.

```markdown
## Step N: Structural Validation

For each generated item, verify:
- [ ] All required fields populated (title, description, category, date)
- [ ] Field values match allowed enums (e.g., category ∈ {Highlight, Observation, Risk})
- [ ] Dates are valid ISO format
- [ ] IDs match expected patterns (e.g., 18-char SFDC ID)
- [ ] Description length > minimum threshold (e.g., 50 chars)
```

For skills with external validation scripts:

```markdown
1. Create temporary draft file
2. Run validation script:
   python3 scripts/validate-draft.py <draft_file>
3. Exit codes: 0 = PASSED, 1 = FAILED (exclude), 2 = WARNINGS (proceed with note)
```

#### Validation Script Output Contract

Scripts MUST print a single JSON object to stdout conforming to this schema:

```json
{
  "status": "PASSED | FAILED | WARNINGS",
  "checked": 5,
  "errors": [
    {
      "field": "category",
      "rule": "enum",
      "message": "'Invalid' is not a valid category. Allowed: [...]"
    }
  ],
  "warnings": [
    {
      "field": "description",
      "rule": "min_length",
      "message": "Description is 12 chars (minimum: 50)"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | `PASSED`, `FAILED`, or `WARNINGS` — must match exit code |
| `checked` | integer | Yes | Number of items validated |
| `errors` | array | Yes | Blocking issues (empty array if none) |
| `warnings` | array | Yes | Non-blocking issues (empty array if none) |
| `errors[].field` | string | Yes | Field name that failed (dot notation for nested: `parent_record.id`) |
| `errors[].rule` | string | Yes | Rule that was violated (`required`, `enum`, `min_length`, `sfdc_id_length`, `date_format`) |
| `errors[].message` | string | Yes | Human-readable description |

The agent consumes this output to:
- Populate the summary display with specific failure reasons
- Decide whether to queue (PASSED/WARNINGS) or exclude (FAILED) each item
- Surface warnings to the user during review

See `examples/scripts/validate-draft.py` for a working implementation.

### Tier 2: Confidence Scoring

Assign HIGH/MEDIUM/LOW confidence to every generated item.

```markdown
## Step N: Assign Confidence Levels

**HIGH** — ALL of the following:
- Clear source event with complete context
- All required fields populated and validated
- Linked to SFDC record (opportunity preferred, account minimum)
- No duplicate warnings
- Unambiguous classification

**MEDIUM** — ANY of the following:
- Likely valid but missing one HIGH criterion
- No opportunity match (account-only)
- Ambiguous classification
- Limited source context

**LOW** — ANY of the following:
- Possible but very brief/unclear source
- Missing multiple fields
- Ambiguous whether item is warranted
```

### Tier 3: Gated Submission

Control what gets submitted based on confidence.

| Confidence | Auto-Approve | User Action Required |
|------------|-------------|---------------------|
| HIGH | ✅ Eligible | None (unless user opts for manual review) |
| MEDIUM | ❌ | Review and confirm or edit |
| LOW | ❌ | Review, enrich, or discard |

```markdown
Set `auto_approve_eligible: true` only for HIGH confidence.
```

### Defining Confidence for Your Domain (Meta-Template)

The HIGH/MEDIUM/LOW criteria above are examples from a CRM use case. Every skill needs its own domain-specific criteria. To define confidence for your skill, answer four questions:

1. **What constitutes a complete source input?** (What data must be present for you to trust the finding?)
2. **What external record must be linked for full trust?** (What system-of-record validates the finding?)
3. **What ambiguity would make you hesitate to submit without human review?** (What uncertainty drops confidence?)
4. **What would make you discard the item entirely?** (What makes a finding not worth queuing?)

**Worked examples across three domains:**

**Example A: CRM Activity Logger**
| Question | Answer | Maps to |
|----------|--------|---------|
| Complete source? | Calendar event with customer attendees + meeting notes or email thread | HIGH requires both event + notes |
| External record? | SFDC opportunity linked (not just account) | HIGH requires opp; MEDIUM = account-only |
| Ambiguity? | Activity type unclear (Demo vs. Architecture Review?) | MEDIUM |
| Discard? | <15 min meeting, no customer attendees, no notes | LOW or exclude |

**Example B: File Cleanup / Memory Management**
| Question | Answer | Maps to |
|----------|--------|---------|
| Complete source? | File exists, last-accessed date available, size known | HIGH requires all three |
| External record? | File is not referenced by any active config or script | HIGH requires no references found |
| Ambiguity? | File referenced in a comment but not in code | MEDIUM |
| Discard? | File modified in last 7 days, or is a dotfile/config | Exclude |

**Example C: Presentation Builder**
| Question | Answer | Maps to |
|----------|--------|---------|
| Complete source? | Slide has title, content, and speaker notes; follows brand rules | HIGH requires all three + brand pass |
| External record? | Content sourced from approved document (not hallucinated) | HIGH requires traceable source |
| Ambiguity? | Content inferred from partial notes, no direct source quote | MEDIUM |
| Discard? | Slide violates brand rules after two correction attempts | Exclude and flag |

---

## 5. Skill Composition

Production systems rarely use a single skill in isolation. Skills chain together — a generator produces a queue, a reviewer presents it for approval, a submitter writes to external systems. This section covers how to design skills that compose reliably.

### Dependency Declaration

Skills that depend on another skill having run first SHOULD declare this in their SKILL.md:

```markdown
## Dependencies

- **Requires:** `sa-activity-generator` must have run first (produces `pending-activities.json`)
- **Reads from:** `~/.aim-data/sa-activity-queue/pending-activities.json`
- **Writes to:** `~/.aim-data/sa-activity-queue/logs/submitted-activities.json`
```

This is documentation, not enforcement — the agent reads it and checks for the required files at Step 0.

### Queue Files as the Inter-Skill Contract

The queue JSON file is the data contract between skills. Both the producer and consumer must agree on the schema.

```
┌─────────────────┐    pending-items.json    ┌─────────────────┐    external API    ┌──────────┐
│   Generator     │ ──────────────────────► │   Queue/Review  │ ─────────────────► │  Submit  │
│   (produces)    │                          │   (presents)    │                    │  (writes)│
└─────────────────┘                          └─────────────────┘                    └──────────┘
```

Rules:
- The generator owns the schema — it defines the `drafts[]` structure
- The reviewer reads the schema but never modifies it (only adds user decisions: approve/edit/dismiss)
- The submitter maps from the queue schema to the external system's API
- Schema changes in the generator require updates to downstream skills

### Shared State Access

When multiple skills read/write the same data directory:

| Pattern | Example | Rule |
|---------|---------|------|
| One writer, many readers | Generator writes queue; reviewer and submitter read it | Safe — no conflicts |
| Sequential writers | Generator writes, then reviewer appends decisions | Safe — skills don't run concurrently |
| Concurrent writers | Two generators writing to the same queue | **Avoid** — use separate queue files |

### Error Propagation Across Skill Boundaries

When skill A fails, what happens to skill B?

- **Skill A fails before writing queue:** Skill B has nothing to process. Skill B's Step 0 checks for the queue file and reports "no pending items."
- **Skill A writes partial queue then fails:** Skill B processes whatever is in the queue. The queue file is the contract — if it's valid JSON with valid items, it's consumable regardless of whether skill A completed all its steps.
- **Skill B fails mid-submission:** Skill B's submission log tracks what was already submitted. On retry, it picks up where it left off (idempotent by design).

### External Tool Dependencies (MCP Servers)

Skills that depend on MCP servers (e.g., a presentation skill needing `pptx-server`) should verify tool availability in Step 0 as a pre-flight check. This is a runtime concern, not a data contract — the skill doesn't own the MCP server, it just needs it to be running.

```markdown
## Step 0: Pre-flight Check

1. Verify required MCP tools are available:
   - Call `inspect_template` with a known path — if it fails, STOP and inform user:
     "pptx-server is not running. Start it or restart kiro-cli."
2. Check state file for last run...
```

If an MCP tool fails mid-execution, the Error Transparency Protocol (section 7) applies — STOP → INFORM → EXPLAIN → PROCEED.

---

## 6. State Persistence

Skills that run periodically MUST track state to avoid duplicate processing.

### State File Pattern

Store state in a dedicated data directory **separate from your skill definitions**. If your skills are managed by a platform that pushes updates, skill definition files can get overwritten. Runtime data (queues, state, logs) must survive those updates.

```
<skill-data-dir>/<skill-name>/.last-run
```

Content:
```
Last run: 2026-04-01T16:00:00-07:00
Scan period: 2026-03-25 to 2026-04-01 (7 days)
Items scanned: 42
Items generated: 5
Items queued: 3
```

### Rules

- **NEVER** co-locate runtime data with skill definition files (platform updates may overwrite them)
- **ALWAYS** use a dedicated data directory separate from skill definitions
- **ALWAYS** update state even if no items were generated
- Use `.last-run` timestamp to auto-calculate next scan window
- Store queued items in `<skill-data-dir>/<skill-name>/pending-<type>.json`
- Store submission logs in `<skill-data-dir>/<skill-name>/logs/submitted-<type>.json`

### Duplicate Detection

Before adding to queue, check submission logs:
```markdown
For each candidate:
1. Search submitted-findings.json for matching title + account + date (±3 days)
2. If >85% similarity → mark as DUPLICATE, exclude
3. If 50-85% similarity → mark as UPDATE, include with reference to original
4. If <50% similarity → mark as CREATE
```

---

## 7. Error Transparency Protocol

When tool operations fail, the agent MUST follow this sequence:

```
1. STOP  — Do not silently continue
2. INFORM — Tell user what failed and why
3. EXPLAIN — Describe recovery approach
4. PROCEED — Only then attempt the fix
```

### Examples

❌ Wrong:
```
[Tool fails] → [Silently retries] → "Done!"
```

✅ Correct:
```
[Tool fails] → "I looked for pending-sifts.json but it doesn't exist yet.
This appears to be the first run. Creating a new queue file..." → [Creates file] → "Done!"
```

PROCEED is the right choice when the failure is recoverable without data loss. For failures that occur after the skill has already modified files or external systems, see **§8 Rollback & Recovery** for additional recovery options (HALT, ROLLBACK).

---

## 8. Rollback & Recovery

STRICT mode (§2) guarantees steps execute in order. Error Transparency (§7) guarantees failures are communicated. Neither addresses what happens when step 4 of 6 fails *after steps 1-3 already modified state*. This section closes that gap.

### The Problem

A skill that modifies files, writes to external systems, or builds artifacts incrementally can leave inconsistent state on mid-execution failure. Examples:
- A file cleanup skill deletes 3 of 6 files, then fails on file 4
- A presentation skill builds 5 of 8 slides, then the MCP server crashes
- A queue submission skill submits 2 of 4 items to SFDC, then hits a permissions error

Without rollback guidance, the agent either silently continues (bad) or halts with no way to recover (frustrating).

### Extended Error Transparency Protocol

When a failure occurs after state has been modified, the Error Transparency Protocol (§7) extends from four steps to five:

```
1. STOP     — Do not silently continue
2. INFORM   — Tell user what failed and why
3. EXPLAIN  — Describe what state was modified before the failure
4. OFFER    — Present recovery options:
               → PROCEED  (retry/continue from current state)
               → HALT     (stop, keep partial state, checkpoint preserved)
               → ROLLBACK (restore to a previous checkpoint)
5. EXECUTE  — Carry out the user's choice
```

### Checkpointing

Skills that perform destructive or incremental operations SHOULD checkpoint state before each destructive step.

**Checkpoint storage:**
```
~/.aim-data/<skill>/checkpoints/<session-id>/
├── step-2.snapshot       # State before step 2 executed
├── step-4.snapshot       # State before step 4 executed
└── manifest.json         # Maps steps to snapshots
```

**Manifest schema:**
```json
{
  "session_id": "deck-2026-04-22-1045",
  "created_at": "2026-04-22T10:45:00-07:00",
  "checkpoints": [
    {
      "step": 2,
      "description": "Before adding slide 3",
      "snapshot_file": "step-2.snapshot",
      "artifact": "~/Documents/archer-qbr.pptx",
      "timestamp": "2026-04-22T10:46:12-07:00"
    },
    {
      "step": 4,
      "description": "Before adding slide 5",
      "snapshot_file": "step-4.snapshot",
      "artifact": "~/Documents/archer-qbr.pptx",
      "timestamp": "2026-04-22T10:47:30-07:00"
    }
  ]
}
```

### What to Checkpoint

Not every step needs a checkpoint. Only checkpoint before operations that modify state the user cares about:

| Operation Type | Checkpoint? | Example |
|---------------|-------------|---------|
| Read-only (scan, search, fetch) | No | Scanning emails, reading files |
| Queue write (local JSON) | Optional | Writing pending-items.json (easy to regenerate) |
| File modification | **Yes** | Adding slides to a .pptx, editing documents |
| External system write | **Yes** | Submitting to SFDC, sending emails |
| Destructive (delete, overwrite) | **Yes** | Deleting files, overwriting configs |

### Snapshot Format

The snapshot is a copy of the artifact at that point in time. The format depends on the skill:

- **File-based skills (presentations, documents):** Copy the file → `step-N.snapshot` (binary copy)
- **Queue-based skills:** Copy the JSON queue file → `step-N.snapshot`
- **External system skills:** Log what was submitted (can't truly rollback external writes, but can track for manual reversal)

### Recovery Options

When offering recovery after a failure:

**PROCEED** — Retry the failed step or skip it and continue.
- Use when: The failure is transient (network timeout, rate limit) or the step is non-critical.
- State: Unchanged from point of failure.

**HALT** — Stop execution, keep partial state, preserve checkpoints.
- Use when: The user needs to investigate or fix something before continuing.
- State: Partial — some steps completed, checkpoints available for later rollback.
- The user can resume later or rollback.

**ROLLBACK** — Restore a previous checkpoint and optionally continue from there.
- Use when: The partial state is worse than a previous state (e.g., a bad slide was added, a wrong record was submitted).
- State: Restored to the selected checkpoint.
- The user picks which checkpoint to restore to.

### User-Initiated Rollback

Rollback isn't only for error recovery. Users may request rollback during normal operation:

```
User: "Undo the last slide"
Agent: [Restores checkpoint from before last slide was added]
       [Continues from restored state]

User: "Roll back to after slide 2"
Agent: [Restores checkpoint-step-2]
       [Shows current state: 2 slides]
       "Rolled back to after slide 2. Continue building from here?"
```

### Checkpoint Lifecycle

- **Create:** Before each destructive step
- **Retain:** For the duration of the session (or until the user explicitly clears them)
- **Clean up:** On successful completion, offer to delete checkpoints:
  ```
  "Presentation saved. Delete 6 checkpoints (12 MB)? [y/n]"
  ```
- **Persist across sessions:** Checkpoints survive session restarts. If the user comes back tomorrow, they can still rollback.

### Declaring Rollback Support

Skills that support rollback SHOULD declare it in their SKILL.md:

```markdown
## Rollback Support

This skill checkpoints before each slide modification.
- Checkpoints: `~/.aim-data/aws-presentation-builder/checkpoints/<session-id>/`
- Commands: `undo last slide`, `roll back to after slide N`
- Cleanup: Offered on successful save
```

---

## 9. Summary Display

Every skill MUST end with a structured summary.

### Template

```
═══════════════════════════════════════════════════════════
✅ [SKILL NAME] COMPLETE
═══════════════════════════════════════════════════════════

Scan Period: [start] to [end] ([N] days)

Data Sources:
  • [N] emails
  • [M] meetings
  • [P] documents

Results: [Q] items generated
  • 🟢 [X] HIGH confidence
  • 🟡 [Y] MEDIUM confidence
  • 🔴 [Z] LOW confidence

Duplicates: [N] excluded
Queue: ~/.aim-data/<skill>/pending-<type>.json

Next: `<command to review queue>`
═══════════════════════════════════════════════════════════
```

---

## 10. Quick Reference: Skill Authoring Checklist

- [ ] `SKILL.md` with YAML frontmatter (name, description)
- [ ] `README.md` with human-readable overview
- [ ] `CHANGELOG.md` with version history
- [ ] `## Execution Mode: STRICT` declared
- [ ] Execution Plan Display with numbered checkboxes
- [ ] Steps numbered sequentially (`## Step 0:` through `## Step N:`)
- [ ] Validation: structural checks on all generated output
- [ ] Validation: confidence scoring (HIGH/MEDIUM/LOW) with explicit criteria
- [ ] Validation: gated submission (only HIGH auto-approves)
- [ ] State persistence via `~/.aim-data/<skill>/.last-run`
- [ ] Duplicate detection against submission logs
- [ ] Error transparency (STOP → INFORM → EXPLAIN → PROCEED)
- [ ] Summary display at completion
- [ ] Data paths documented (queue, logs, state)
- [ ] `scripts/` directory for any validation or automation scripts
- [ ] Scripts return JSON and use exit codes (0=pass, 1=fail, 2=warn)
- [ ] Rollback: destructive steps identified and checkpointed (§8)
- [ ] Rollback: PROCEED/HALT/ROLLBACK options offered on mid-execution failure
- [ ] Rollback: checkpoint cleanup offered on successful completion

---

## 11. Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| No execution mode declared | Agent skips steps, reorders, assumes | Add `## Execution Mode: STRICT` |
| Steps not numbered | Agent can't track progress, user can't verify | Use `## Step N:` format |
| No validation before submission | Bad data reaches SFDC/external systems | Add 3-tier validation |
| Silent error recovery | User doesn't know what went wrong | Add error transparency protocol |
| State in skill definitions dir | Gets overwritten by platform updates | Use a separate data directory |
| Vague confidence criteria | Everything becomes MEDIUM | Define explicit HIGH/MEDIUM/LOW rules with examples |
| No duplicate detection | Same item submitted multiple times | Check submission logs before queuing |
| No summary at end | User doesn't know what happened | Add structured summary display |
| No checkpoints before destructive steps | Can't recover from mid-execution failure | Checkpoint before file/system modifications (§8) |
| Rollback only on error | User can't undo intentional but wrong changes | Support user-initiated rollback too |
| Checkpoints never cleaned up | Disk fills with stale snapshots | Offer cleanup on successful completion |

---

*This guide extends the Anthropic Agent Skills Open Standard (Dec 2025) with enterprise execution patterns. v1.1 adds skill composition, rollback/recovery, generalized confidence scoring, and validation script contracts. Compatible with any SKILL.md-based agent framework.*
