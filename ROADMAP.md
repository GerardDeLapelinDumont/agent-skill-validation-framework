# Roadmap

## Agent Skill Validation Framework

### v1.0 (Released — April 2026)
- [x] STRICT Execution Mode
- [x] Execution Plan Display
- [x] Three-Tier Validation (structural, confidence, gated submission)
- [x] Cross-Session State Persistence
- [x] Error Transparency Protocol
- [x] Summary Display

### v1.1 (Current — April 2026)
- [x] Confidence meta-template (domain-agnostic 4-question framework)
- [x] Validation script data contract (JSON schema for script output)
- [x] Skill composition (dependency declaration, queue-as-contract, error propagation)
- [x] Rollback & Recovery (checkpointing, HALT/ROLLBACK options, user-initiated undo)
- [x] Examples directory (reference SKILL.md, validate-draft.py, sample state files)
- [x] CI (GitHub Action for markdown lint + Python syntax check)

### v1.2 (Planned)
- [ ] Validation script library (reusable validators for common patterns: SFDC IDs, dates, enums)
- [ ] Confidence calibration (track predicted vs. actual confidence over time)
- [ ] Cross-skill state coordination (formal protocol for concurrent skill access)
- [ ] Checkpoint compression (deduplicate binary snapshots for large artifacts)

### Future / Exploratory
- [ ] Agent-to-agent skill delegation (skill A invokes skill B as a sub-routine)
- [ ] Automated regression testing for skills (replay past inputs, compare outputs)
- [ ] Skill versioning and migration (handle schema changes across skill versions)
- [ ] Telemetry integration (track step-skipping rates, validation pass rates, rollback frequency)

---

*Items move from Future → Planned → Current based on production need. PRs welcome for any item.*
