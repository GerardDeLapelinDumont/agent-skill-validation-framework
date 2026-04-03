# From Probabilistic to Predictable: A Validation Framework for AI Agent Skills

*How a 3-tier validation layer on top of the Anthropic Agent Skills standard turned our AI agent workflows from "works most of the time" to "works every time."*

*By Gerard De Lapelin Dumont and an AI field assistant (co-author)*

---

Anthropic released the Agent Skills open standard in December 2025. It solved a real problem — modular, reusable expertise for AI agents without bloating every request with redundant instructions. A month later, AWS introduced Agent SOPs — markdown-based procedures using RFC 2119 keywords (MUST, SHOULD, MAY) to constrain agent behavior.

Both are great. We use both. And after six months of building production skills on top of them, we can tell you: they're not enough.

Skills tell the agent *what* to do. SOPs tell the agent *how* to behave. Neither tells the agent — or you — whether the output is *good enough to trust*.

This is the story of how we built a validation framework to close that gap, and the actual numbers that convinced us it was worth the effort.

---

## The Problem We Kept Hitting

We build agent skills for enterprise workflows — the kind where the agent scans your emails, extracts customer interactions, and writes structured records to a CRM. Not chatbot stuff. Production data pipelines where bad output has real consequences.

Our skills followed the Anthropic standard. Clean SKILL.md files, YAML frontmatter, progressive disclosure, executable scripts. They worked. Mostly.

"Mostly" was the problem. We tracked three failure modes over our first 8 weeks of production use:

**Step skipping.** The agent would read a 12-step skill, decide steps 5 and 6 were "redundant," and skip them. Step 5 was duplicate detection. Step 6 was CRM record linking. Both were critical. The agent didn't know that because it was optimizing for speed, not correctness.

**Silent error recovery.** A file-not-found error? The agent would quietly search for an alternative and keep going. An API timeout? Silent retry. The output looked fine. It wasn't. We'd discover missing data days later when someone asked "why isn't this customer interaction in the CRM?"

**Everything submitted at the same confidence.** The agent would generate 10 findings from an email scan. Three were solid — clear customer interaction, full context, linked to an opportunity. Four were reasonable but missing details. Three were speculative at best. All 10 got submitted. No distinction between "I'm certain" and "this might be something."

The MTHDS open standard project nailed the diagnosis: "Skills guide intent. They don't guarantee execution."

We needed something between "skill executed" and "output submitted."

---

## What We Built: Three Extensions

Our framework adds three capabilities to any SKILL.md-based skill. Each is independent — adopt one without the others — but they compound when used together.

### Extension 1: STRICT Execution Mode

LLMs are non-deterministic. Same skill, same input, different execution path. STRICT mode fights this with an explicit contract.

Every skill declares it right after the commands table:

```markdown
## Execution Mode: STRICT

**Before executing ANY tools:**
1. Read this ENTIRE skill file
2. Follow each step IN ORDER
3. Do NOT skip steps
4. Do NOT make assumptions
```

Before any tool calls, the agent displays a numbered plan:

```
═══════════════════════════════════════════════════════════
CUSTOMER INTERACTION SCANNER
═══════════════════════════════════════════════════════════

EXECUTION PLAN:
 ☐ Step 0: Check last run state
 ☐ Step 1: Load customer context
 ☐ Step 2: Scan emails
 ☐ Step 3: Scan calendar
 ☐ Step 4: Extract findings
 ☐ Step 5: Check for duplicates
 ☐ Step 6: Link to CRM records
 ☐ Step 7: Run validation
 ☐ Step 8: Assign confidence
 ☐ Step 9: Queue results
 ☐ Step 10: Update state
 ☐ Step 11: Show summary
```

Two things happen here. First, the agent commits to a sequence before starting — reducing ad-hoc reordering. Second, the user gets a visible contract. If Step 5 doesn't show up in the output, you know something was skipped.

Is it foolproof? No. But in our testing, step-skipping dropped from roughly 1-in-4 runs to fewer than 1-in-20.

**How this relates to AWS Agent SOPs:** SOPs use MUST/SHOULD/MAY for per-step constraints. STRICT mode constrains the execution *sequence*. They're complementary — use STRICT for ordering, RFC 2119 for per-step rules.

### Extension 2: Three-Tier Validation

This is the core of the framework. Every skill that writes to an external system implements three validation tiers before anything gets submitted.

**Tier 1: Structural Validation (Code, Not Language)**

Programmatic checks that fields exist and conform to expected formats. This follows Anthropic's own recommendation — use deterministic scripts for deterministic work.

```python
# scripts/validate-draft.py
# Exit 0 = PASSED, 1 = FAILED (exclude), 2 = WARNINGS (proceed)

import json, sys

ALLOWED_CATEGORIES = ["Highlight", "Observation", "Risk", "Challenge"]

def validate(draft):
    errors = []
    if len(draft.get("description", "")) < 50:
        errors.append("Description under 50 chars")
    if draft.get("category") not in ALLOWED_CATEGORIES:
        errors.append(f"Invalid category: {draft['category']}")
    if not draft.get("account_id", "").startswith("001"):
        errors.append("Bad account ID format")
    return errors

draft = json.loads(open(sys.argv[1]).read())
errors = validate(draft)
sys.exit(1 if errors else 0)
```

The agent doesn't interpret validation results. It reads exit codes. 0 = passed. 1 = failed, item excluded. 2 = warnings, proceed but flag. Deterministic code doing deterministic work.

**Tier 2: Confidence Scoring**

Every generated item gets a confidence level with explicit, domain-specific criteria:

| Level | Criteria | What Happens |
|-------|----------|-------------|
| **HIGH** | Clear source event + complete context + CRM record linked + all fields validated + unambiguous classification | Auto-approve eligible |
| **MEDIUM** | Likely valid but missing one HIGH criterion (no CRM link, ambiguous type, limited context) | Human review required |
| **LOW** | Speculative — brief interaction, missing multiple fields, unclear if item is warranted | Enrich or discard |

The criteria must be specific to your domain. "Complete context" means something different for an email scanner (full thread available) versus a meeting logger (agenda + attendees + notes all present). Vague criteria → everything becomes MEDIUM → framework is useless.

**Tier 3: Gated Submission**

The skill that *generates* items is optimized for recall — don't miss anything. The skill that *submits* items is optimized for precision — don't submit garbage. They're separate skills connected by a validated queue file.

The generator sets `auto_approve_eligible: true` only for HIGH confidence items. A separate queue management skill handles review and submission. The generator never writes directly to external systems.

### Extension 3: Cross-Session State

The Anthropic standard explicitly calls out "no cross-session state" as a limitation. For one-shot skills, that's fine. For skills that run daily or weekly, it's a dealbreaker.

Without state, the agent doesn't know when it last ran. It re-processes the same emails. It can't detect duplicates against previously submitted items.

Our fix is simple — local state files in a dedicated data directory that's separate from your skill definitions:

```
<skill-data-dir>/<skill-name>/.last-run          # Timestamp + scan metadata
<skill-data-dir>/<skill-name>/pending-items.json  # Queue awaiting review
<skill-data-dir>/<skill-name>/logs/submitted.json # Submission history for dedup
```

One important design decision: **keep your skill data separate from your skill definitions.** If your skills are managed by a platform that pushes updates (and most agent frameworks do), your skill definition files can get overwritten. Queues, state files, and submission logs need to live somewhere that survives those updates. We use a sibling directory to our skill definitions — same parent, different folder. Pick whatever works for your setup, but don't co-locate runtime data with skill source files.

The `.last-run` file auto-calculates the next scan window. The submission log enables duplicate detection:

```
For each candidate:
1. Check submitted.json for matching title + account + date (±3 days)
2. >85% match → DUPLICATE, exclude
3. 50-85% match → UPDATE, include with reference to original
4. <50% match → CREATE, new item
```

No database. No API. Just the local filesystem turning a stateless skill into a stateful workflow.

---

## The Numbers

We've been running this framework across 5 production skills for about 10 weeks. Here's what the data shows.

### Skill 1: CRM Activity Logger

Scans emails, calendar, and meeting notes to generate structured activity records for a CRM.

**Before the framework (weeks 1-4):**
- Agent generated activities and submitted them directly
- No confidence scoring, no validation, no duplicate detection
- ~30% of submitted activities needed manual correction after the fact
- Duplicate activities appeared when the skill ran on overlapping date ranges
- Step skipping caused missed CRM record linking on ~25% of runs

**After the framework (weeks 5-10):**
- 23 activities submitted through the validated queue
- 100% were HIGH confidence at time of submission
- 3 MEDIUM confidence items currently in queue awaiting review (not auto-submitted)
- 0 duplicates submitted (dedup caught overlapping items across runs)
- 0 post-submission corrections needed

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Post-submission corrections | ~30% | 0% | ✅ Eliminated |
| Duplicate submissions | Frequent | 0 | ✅ Eliminated |
| Step-skipping incidents | ~25% of runs | <5% of runs | ✅ 80% reduction |
| Items needing manual review | 0 (everything auto-submitted) | 3 of 26 (12%) | ✅ Only uncertain items flagged |

### Skill 2: Field Insight Generator

Scans emails, calendar, and customer documents to generate field insights (structured observations about customer trends).

**Production data from a single run (8-day scan window):**
- 39 emails scanned (25 inbox, 14 sent)
- 60+ calendar events processed
- 51 OneDrive documents analyzed
- 8 findings generated
- Confidence breakdown: 5 HIGH, 2 MEDIUM, 0 LOW
- 1 duplicate detected (marked as UPDATE instead of CREATE)
- 7 net-new items queued for review

The 2 MEDIUM items were missing opportunity links — the agent flagged them for human review instead of submitting incomplete records. Before the framework, all 8 would have been submitted, and someone would have noticed the missing links later. Or not.

### Skill 3: Meeting Notes Logger

Processes calendar events and generates structured meeting notes in customer document folders.

**Quality validation catches (Step 8 in the skill):**
- Content validation: title clarity, attendee completeness, substantive notes
- Format validation: filename convention, template compliance, markdown validity
- Data validation: customer name matches context file, storage path correct
- Security validation: no PII in filenames

In one run processing 3 meetings, the validation step caught a filename that didn't follow the naming convention. The agent flagged it, asked "Fix issues?", corrected it, and continued. Without validation, the file would have been saved with an inconsistent name — minor, but it compounds across hundreds of files.

### Aggregate Impact

Across all 5 skills over 10 weeks:

| Metric | Value |
|--------|-------|
| Total items generated | ~90 |
| Items submitted (HIGH confidence) | 23 |
| Items in review queue (MEDIUM) | 12 |
| Items discarded (LOW or failed validation) | ~5 |
| Duplicates caught | 4 |
| Post-submission corrections needed | 0 |
| Step-skipping incidents (with STRICT mode) | <5% of runs |

The most important number: **0 post-submission corrections**. Before the framework, we were fixing CRM records after the fact roughly once a week. That's not a lot, but each correction required finding the bad record, understanding what went wrong, and manually fixing it. The framework eliminated that entirely.

---

## The Error Transparency Protocol

One more pattern worth its own section.

LLMs naturally recover from errors silently. File not found? Search for an alternative. API error? Retry. The user sees "Done!" and doesn't know half the data is missing.

We enforce four steps:

```
1. STOP    — Don't silently continue
2. INFORM  — Tell the user what failed
3. EXPLAIN — Describe the recovery approach
4. PROCEED — Only then attempt the fix
```

In practice:

```
❌ Wrong:
[File not found] → [silently searches] → "Done!"

✅ Correct:
[File not found] → "I looked for pending-queue.json but it 
doesn't exist. This appears to be the first run. Creating 
a new queue file..." → [creates file] → continues
```

Seems minor. It's not. When users see every failure and recovery, they trust the output. When failures are hidden, they don't — and they shouldn't.

---

## How This Maps to Existing Standards

We didn't build a replacement. We built a layer.

| Capability | Anthropic Skills | AWS Agent SOPs | Our Framework |
|---|---|---|---|
| Modular structure (SKILL.md) | ✅ | — | ✅ Compatible |
| Progressive disclosure | ✅ | — | ✅ Compatible |
| Script execution | ✅ | ✅ | ✅ + exit code protocol |
| Per-step constraints (MUST/SHOULD/MAY) | — | ✅ | Complementary |
| Execution sequence enforcement | — | — | ✅ STRICT mode |
| Execution plan display | — | — | ✅ |
| Structural validation (Tier 1) | — | — | ✅ |
| Confidence scoring (Tier 2) | — | — | ✅ |
| Gated submission (Tier 3) | — | — | ✅ |
| Cross-session state | ❌ Acknowledged gap | — | ✅ |
| Duplicate detection | — | — | ✅ |
| Error transparency | — | — | ✅ |

Everything in the "Our Framework" column is additive. A skill built with our extensions is still a valid Anthropic Agent Skill. You can use STRICT mode with AWS Agent SOPs. Nothing conflicts.

---

## When to Use This (Honestly)

**Use it when:**
- Your skill writes to external systems (CRM, databases, file systems)
- Your skill runs on a schedule (daily scans, weekly reports)
- Bad output has consequences beyond "that's annoying"
- You need to explain to someone what the agent did and why

**Don't use it when:**
- Your skill answers questions or drafts text for human review
- It's a one-shot task (look something up, summarize a document)
- The overhead of validation exceeds the cost of occasional bad output

The framework has real overhead. STRICT mode adds ~200 tokens. Execution plans add a visible step. Validation scripts need maintenance. State files need a storage location. For a skill that drafts an email, this is overkill. For a skill that writes 23 records to your CRM, it pays for itself on the first run.

---

## Getting Started

If you want to try this, start small:

1. **Pick one skill** that writes to an external system
2. **Add confidence scoring** (Tier 2) — define explicit HIGH/MEDIUM/LOW criteria for your domain, gate submission on confidence
3. **Add STRICT mode** — declare it, add the execution plan display, see if step-skipping decreases
4. **Add state persistence** — implement `.last-run` and duplicate detection
5. **Measure** — track post-submission corrections before and after

Each layer is independent. Adopt incrementally. If confidence scoring alone cuts your correction rate, you might not need the rest.

---

## What's Next

Three things we're working on:

**Validation script libraries.** Reusable validators for common patterns — CRM field formats, date checking, duplicate detection algorithms. Package them so any skill can reference them.

**Confidence calibration.** Tracking actual outcomes (accepted, rejected, edited by human) against predicted confidence. If HIGH items get edited 30% of the time, the criteria are too loose. We want a feedback loop.

**Cross-skill state.** Today each skill has its own state. But skills that share a domain — email scanner, meeting logger, activity generator — would benefit from shared state. "This email was already processed by the meeting logger, don't re-extract it as an activity."

---

## The Takeaway

The Anthropic Agent Skills standard and AWS Agent SOPs solved the hard structural problems — how to package expertise, how to constrain behavior, how to make skills portable and composable. That foundation is solid.

What was missing was the trust layer. The thing that lets you run a skill against production data and know — not hope, know — that the output meets a quality bar before it reaches your systems.

Skills guide intent. Validation guarantees quality.

The full framework spec is open source at [github.com/GerardDeLapelinDumont/agent-skill-validation-framework](https://github.com/GerardDeLapelinDumont/agent-skill-validation-framework). It's a single markdown file you can drop into any SKILL.md-based project. We'd love feedback, contributions, and war stories from anyone building production agent skills.

---

*Gerard De Lapelin Dumont is a Solutions Architect who builds AI agent workflows for enterprise customers. The AI field assistant that co-authored this article is the same agent that runs the skills described in it. The framework was developed through daily production use across 5 skills over 10 weeks. All metrics are from actual production data. Opinions are the authors' own.*
