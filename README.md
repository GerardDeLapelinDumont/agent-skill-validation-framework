# Agent Skill Validation Framework

A validation layer for AI agent skills that extends the [Anthropic Agent Skills Open Standard](https://agentskills.io) with execution enforcement, confidence-gated submission, and cross-session state.

## The Problem

AI agent skills tell the agent *what* to do. SOPs tell the agent *how* to behave. Neither tells the agent — or you — whether the output is *good enough to trust*.

This framework closes that gap with six extensions:

1. **STRICT Execution Mode** — Enforces step ordering, displays execution plans, reduces step-skipping from ~25% to <5% of runs
2. **Three-Tier Validation** — Structural validation (code), confidence scoring (domain-specific), and gated submission (separate generate vs. submit)
3. **Cross-Session State** — Local state files for scan windows, duplicate detection, and submission history
4. **Rollback & Recovery** — Checkpointing before destructive operations, HALT/ROLLBACK options on failure, user-initiated undo
5. **Skill Composition** — Dependency declaration between skills, queue-as-contract pattern, error propagation across skill boundaries
6. **Confidence Meta-Template** — Domain-agnostic 4-question framework for defining confidence criteria, plus a JSON schema data contract for validation scripts

## Production Results

Across 5 production skills over 10 weeks:

| Metric | Before | After |
|--------|--------|-------|
| Post-submission corrections | ~30% | 0% |
| Duplicate submissions | Frequent | 0 |
| Step-skipping incidents | ~25% of runs | <5% of runs |

## Compatibility

Fully compatible with:
- [Anthropic Agent Skills Open Standard](https://agentskills.io) — all extensions are additive
- [Agent SOPs](https://github.com/strands-agents/agent-sops) — STRICT mode complements RFC 2119 constraints

A skill built with this framework is still a valid Anthropic Agent Skill.

## Quick Start

1. Read the [Skill Authoring Guide](docs/skill-authoring-guide.md) — the complete framework spec
2. Study the [reference skill](examples/reference-skill/SKILL.md) — a fully annotated example with all v1.1 patterns
3. Review the [validation script](examples/scripts/validate-draft.py) — structural validation with JSON data contract
4. Add `## Execution Mode: STRICT` to your SKILL.md
5. Define domain-specific confidence criteria using the 4-question meta-template
6. Separate your generator skill from your submission skill
7. Add rollback checkpoints before any destructive operations

## Documentation

- [Skill Authoring Guide](docs/skill-authoring-guide.md) — Full framework specification
- [Reference Skill](examples/reference-skill/SKILL.md) — Annotated SKILL.md with all patterns
- [Validation Script](examples/scripts/validate-draft.py) — Example structural validator with JSON data contract
- [Examples](examples/) — State files, logs, and sample outputs
- [Roadmap](ROADMAP.md) — What's shipped and what's planned

## Related

- [Blog Post: From Probabilistic to Predictable](https://medium.com/@gerarddldumont/from-probabilistic-to-predictable-a-validation-framework-for-ai-agent-skills-95b463022dfb) — Detailed writeup with production metrics

## License

MIT

## Contributing

Issues and PRs welcome. If you're building production agent skills and have patterns to share, we'd love to hear from you.
