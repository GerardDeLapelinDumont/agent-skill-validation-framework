# Agent Skill Validation Framework

A validation layer for AI agent skills that extends the [Anthropic Agent Skills Open Standard](https://agentskills.io) with execution enforcement, confidence-gated submission, and cross-session state.

## The Problem

AI agent skills tell the agent *what* to do. SOPs tell the agent *how* to behave. Neither tells the agent — or you — whether the output is *good enough to trust*.

This framework closes that gap with three extensions:

1. **STRICT Execution Mode** — Enforces step ordering, displays execution plans, reduces step-skipping from ~25% to <5% of runs
2. **Three-Tier Validation** — Structural validation (code), confidence scoring (domain-specific), and gated submission (separate generate vs. submit)
3. **Cross-Session State** — Local state files for scan windows, duplicate detection, and submission history

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
- [AWS Agent SOPs](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-sop.html) — STRICT mode complements RFC 2119 constraints

A skill built with this framework is still a valid Anthropic Agent Skill.

## Quick Start

1. Read the [Skill Authoring Guide](docs/skill-authoring-guide.md) — the complete framework spec
2. Check the [examples/](examples/) directory for reference implementations
3. Add `## Execution Mode: STRICT` to your SKILL.md
4. Define domain-specific confidence criteria (HIGH/MEDIUM/LOW)
5. Separate your generator skill from your submission skill

## Documentation

- [Skill Authoring Guide](docs/skill-authoring-guide.md) — Full framework specification
- [Examples](examples/) — Reference skill implementations

## Related

- [Blog Post: From Probabilistic to Predictable](https://medium.com/@gdumont) — Detailed writeup with production metrics

## License

MIT

## Contributing

Issues and PRs welcome. If you're building production agent skills and have patterns to share, we'd love to hear from you.
