# Tasks: AI Finance Department

Legend: `[P]` can run in parallel · ✅ done · ⬜ open

## Phase 1 — Setup
- ✅ T001 Kit folder `Finance-Agents-Kit/` beside CFO-Cure-Kit and HR-Cure-Kit
- ✅ T002 Constitution `.specify/memory/constitution.md`
- ✅ T003 Spec, plan, research, data model, quickstart

## Phase 2 — Foundation
- ✅ T010 `config/roles.json` (9 roles, job descriptions)
- ✅ T011 `contracts/handoff.schema.json`
- ✅ T012 `config/site.example.json`, `config/site.alfaihaa.json`
- ✅ T013 `rules/_template/`, `rules/alfaihaa/` (7 areas, from the standing rules)
- ✅ T014 `scripts/validate_kit.py`, `scripts/new_period.py`

## Phase 3 — Agents (US1, US2, US3)
- ✅ T020 [P] finance-manager · T021 [P] chief-accountant · T022 [P] internal-auditor
- ✅ T023 [P] ar-insurance · T024 [P] ap-supplier · T025 [P] vat · T026 [P] payroll · T027 [P] cost-inventory · T028 [P] gl
- ✅ T029 `SKILL.md` dispatcher procedure

## Phase 4 — Packaging (FR-012)
- ✅ T030 Back up `build_plugin.py`; add kit as third source + root `agents/`; `.html` only for this kit's templates
- ✅ T031 `scripts/check_build_diff.py` — old packaged files byte-identical
- ⬜ T032 Nightly sync pushes the new snapshot to GitHub (automatic)

## Phase 5 — Page (US5)
- ✅ T040 `templates/finance-office-3d.html` (org chart + 3D office)
- ⬜ T041 v2: feed the page from `run_log.md`

## Phase 6 — Pilot
- ⬜ T050 Confirm missing accounts in `site.alfaihaa.json` (AP control, VAT output/input)
- ✅ T051 Pilot: ar-insurance-accountant + chief-accountant on 2026-10 — approved; 65 vouchers / 1,209,575.79 tie; 1 high + 1 low finding confirmed
- ✅ T051a Kit 1.0.1: fixes from the chief accountant review
- ✅ T052 Tune rules from pilot; enable remaining roles
- ✅ T053a Full-department run 2026-10: 6 roles approved (5 after one return), audit "minor exceptions", summary written
- ✅ T053b Kit 1.1.0 from the run
- ⬜ T053 Full-department run 2026-11
- ⬜ T054 v2: n8n monthly schedule
