# Framework Review — Consolidated Feedback & Action Plan

**Date:** April 17, 2026
**Sources:** Two independent AI reviews (Aire-Neo session + Thane session)
**Status:** Ready for implementation

---

## What's Strong

- The three failure modes (step skipping, silent error recovery, undifferentiated confidence) are real, documented-from-production problems — not theoretical.
- STRICT mode is the highest-value pattern. Simple to implement, massive impact. The execution plan display is the enforcement mechanism — the agent commits publicly before acting.
- Error transparency protocol (STOP → INFORM → EXPLAIN → PROCEED) is excellent. Four words that solve the most dangerous LLM behavior.
- Separating runtime data from skill definitions — a lesson most people learn the hard way, codified upfront.
- The Skill Authoring Guide is genuinely useful as a standalone spec. The checklist, anti-patterns table, wrong-vs-right examples — written by someone who actually builds with these tools.
- Compatibility story is clean — everything additive to Anthropic standard, nothing conflicts with AWS SOPs.
- Production metrics are compelling (0 post-submission corrections across 23 items over 10 weeks).

---

## Feedback: Issues to Address

### 1. Confidence Scoring Doesn't Generalize
**Problem:** HIGH/MEDIUM/LOW criteria are defined purely in CRM/SFDC terms. The blog says "criteria must be specific to your domain" but only gives one domain's criteria. For non-CRM skills (memory management, file operations, etc.), there's no guidance on how to define confidence.

**Action:** Add a confidence meta-template to the Skill Authoring Guide. Something like:
> To define confidence for your skill, answer four questions:
> 1. What constitutes a complete source input?
> 2. What external record must be linked for full trust?
> 3. What ambiguity would make you hesitate to submit without human review?
> 4. What would make you discard the item entirely?

Provide 2-3 worked examples across different domains (CRM, file management, data pipeline).

### 2. No Guidance on Skill Composition
**Problem:** The framework treats each skill as isolated. No guidance on chaining, dependencies, or shared state between skills. Production skills already do this (generator → queue → submission), but it's not formalized.

**Action:** Add a new section to the Skill Authoring Guide covering:
- Dependency declaration ("this skill requires skill X to have run first")
- Shared state access patterns (multiple skills reading/writing the same data directory)
- Error propagation across skill boundaries (skill A fails → impact on skill B)
- Queue files as the inter-skill communication contract

### 3. Validation Script Data Contract is Underspecified
**Problem:** Exit codes (0/1/2) are clear, but there's no contract for what the script should output. No defined JSON schema for error details, failed checks, or warnings. The agent needs structured output to populate summaries and flag issues.

**Action:** Define a standard JSON output contract for validation scripts:
```json
{
  "status": "PASSED|FAILED|WARNINGS",
  "errors": [{"field": "...", "message": "..."}],
  "warnings": [{"field": "...", "message": "..."}]
}
```
Add this to the Skill Authoring Guide and update the `validate-draft.py` example.

### 4. No Rollback/Undo Guidance
**Problem:** STRICT mode guarantees forward progress but has no concept of partial failure recovery. Error Transparency says PROCEED but doesn't distinguish between retry, skip, rollback, or halt. Skills that modify files or external systems can leave inconsistent state on mid-execution failure.

**Action:** Add a "Failure Recovery" section covering:
- Checkpointing: snapshot state before destructive operations
- HALT as an option alongside PROCEED in the Error Transparency Protocol
- Guidance on when to rollback vs. checkpoint-and-halt vs. skip-and-continue
- Example: file cleanup skill that deletes 3 of 6 files before failing

### 5. Empty Examples Directory
**Problem:** README says "Check the examples/ directory for reference implementations" — `examples/scripts/` is empty. The blog has a validator code snippet that isn't in the repo as a runnable file.

**Action:**
- Add a working `examples/scripts/validate-draft.py` (from the blog post snippet)
- Add a complete reference SKILL.md with all extensions applied
- Add sample `.last-run` and `pending-items.json` files showing the expected schema

### 6. No Sample State Files
**Problem:** State persistence section describes file formats in prose but doesn't include concrete examples. Implementers have to reverse-engineer the schema.

**Action:** Add to `examples/`:
- `examples/state/.last-run` — sample with all fields
- `examples/state/pending-items.json` — sample queue file
- `examples/state/logs/submitted.json` — sample submission log with duplicate detection fields

### 7. Duplicate Blog Post Versions
**Problem:** Two versions exist (`blog-post.md` and `blog-post-medium.md`) plus two HTML exports. The Medium version is canonical (README links to it). Creates confusion.

**Action:** Either remove the non-canonical version or add a note at the top of `blog-post.md` pointing to the Medium version as canonical.

### 8. No CI/Tests/Linting
**Problem:** A framework that advocates for validation should validate itself.

**Action:** Add a GitHub Action that checks:
- Markdown formatting/linting
- Link validity
- Example scripts are syntactically valid Python

### 9. No Roadmap
**Problem:** Blog post "What's Next" section promises validation script libraries, confidence calibration, and cross-skill state — but the repo has no tracking for these.

**Action:** Add `ROADMAP.md` or use GitHub Issues to track planned vs. aspirational features.

---

## Suggested Priority Order

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Populate examples directory (#5, #6) | Medium | High — makes the repo actually usable |
| 2 | Confidence meta-template (#1) | Low | High — biggest conceptual gap |
| 3 | Validation script data contract (#3) | Low | Medium — quick spec addition |
| 4 | Skill composition section (#2) | Medium | High — needed for multi-skill systems |
| 5 | Rollback/undo guidance (#4) | Medium | Medium — important for destructive skills |
| 6 | Clean up blog post versions (#7) | Low | Low — housekeeping |
| 7 | Add ROADMAP.md (#9) | Low | Low — sets expectations |
| 8 | Add CI (#8) | Low | Low — nice to have |
