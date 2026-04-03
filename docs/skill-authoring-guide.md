# Skill Authoring Guide: SOP/Validated/Strict Framework

**Version:** 1.0
**Author:** Gerard De Lapelin Dumont
**Date:** April 1, 2026
**Status:** Draft

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

---

## 5. State Persistence

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

## 6. Error Transparency Protocol

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

---

## 7. Summary Display

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

## 8. Quick Reference: Skill Authoring Checklist

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

---

## 9. Anti-Patterns

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

---

*This guide extends the Anthropic Agent Skills Open Standard (Dec 2025) with enterprise execution patterns. Compatible with any SKILL.md-based agent framework.*
