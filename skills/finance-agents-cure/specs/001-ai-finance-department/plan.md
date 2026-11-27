# Implementation Plan: AI Finance Department

**Spec**: `spec.md` · **Constitution**: `../../.specify/memory/constitution.md`

## Technical context
- **Runtime**: Claude Code / Cowork with the `ai-reporting-hub` plugin; sub-agents from the plugin's `agents/`.
- **Data**: Cure MCP (Oracle, one connection per branch), read-only. Discovery on the main branch, same table names elsewhere.
- **Reuse**: CFO-Cure skill (AR, VAT, cost, lease, anomaly scripts), HR-Cure skill (GOSI, commission, letters playbook).
- **Storage**: run outputs on the HUB PC under `Finance-Dept/runs/`. No company data in the plugin.
- **Packaging**: `.plugin-sync/build_plugin.py` gains a third source (`Finance-Agents-Kit` → `skills/finance-agents-cure`) and copies `agents/*.md` to the plugin root.

## Constitution check
| Principle | How the design meets it |
|---|---|
| I Read-only | DB user is read-only; agents have no write path to EXSYS; site config flag gates every run |
| II Maker/checker | Makers → chief-accountant → (auditor) → finance-manager; no self-review |
| III Evidence | schema requires ≥1 evidence item per finding |
| IV Source data | Cure MCP all branches; cancelled excluded; site literals only in config |
| V Additive | new kit folder; build change is additive and diff-checked |
| VI Standing rules | `rules/<site>/` read before every run; findings re-checked |
| VII Human decides | bank files and recommendations staged for people |
| VIII Arabic | all summaries Arabic |

## Architecture
```
user ─▶ main session (SKILL.md = finance-manager dispatcher)
          ├─▶ makers (parallel): ar · ap · vat · payroll · cost · gl ──▶ runs/<p>/<role>/handoff.json
          ├─▶ chief-accountant (per handoff) ──▶ approve / return
          ├─▶ internal-auditor (outputs only) ──▶ audit.md
          └─▶ finance-manager (consolidate) ──▶ summary.md
```

## Project structure (kit)
```
Finance-Agents-Kit/
  SKILL.md  README.md  CHANGELOG.md
  .specify/memory/constitution.md
  specs/001-ai-finance-department/{spec,plan,tasks,data-model,research,quickstart}.md, contracts/
  config/{roles.json, site.example.json, site.alfaihaa.json}
  rules/{_template, alfaihaa}/
  agents/*.md (9)
  templates/finance-office-3d.html
  scripts/{validate_kit.py, new_period.py, check_build_diff.py}
```

## Phases
- **Phase 0** — research (`research.md`): orchestration limits, agent packaging, read-only guarantee.
- **Phase 1** — design: roles registry, handoff contract, site config, rules split.
- **Phase 2** — build: agents, skill, scripts, plugin packaging.
- **Phase 3** — pilot: AR + chief accountant on one month; compare with humans.
- **Phase 4** — roll out remaining roles; v2: n8n schedule, live 3D page fed by `run_log.md`.
