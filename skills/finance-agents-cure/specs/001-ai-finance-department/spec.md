# Feature Specification: AI Finance Department (الإدارة المالية بالذكاء الاصطناعي)

**Feature branch**: `001-ai-finance-department` · **Created**: 2026-11-19 · **Status**: Approved for pilot · **Owner**: Hany Gameel

## Summary
A set of Claude sub-agents that behaves like a well-structured finance department — Finance Manager, Chief Accountant, six role accountants and an independent Internal Auditor — each with a job description and responsibilities, reviewing an EXSYS (Cure) company's books read-only, with maker/checker review and evidence for every finding. It must run unchanged at any company that uses EXSYS, by changing only a site config and a rules folder.

## User scenarios

### US1 — Monthly close review by the team (P1)
The finance lead asks "شغّل الإدارة المالية لشهر أكتوبر". The makers review their areas across all branches, the Chief Accountant approves or returns each file, the Internal Auditor re-tests a sample, and the Finance Manager delivers one Arabic summary.
**Acceptance**: (1) every role produces a handoff that validates against the schema; (2) every finding has evidence; (3) returned items show a reason; (4) summary lists material findings, fixed-since-last-month and open items.

### US2 — One role, one task (P1)
"خلي محاسب الموردين يطابق كشوف نوفمبر". Only that maker and the Chief Accountant run.
**Acceptance**: handoff + review exist for that role only; nothing else is touched.

### US3 — Re-check last month's findings (P1)
Every run marks each earlier finding fixed / partly fixed / still open.
**Acceptance**: no finding from the previous handoff disappears without a status.

### US4 — New EXSYS site (P2)
A second company is onboarded by adding `config/site.<x>.json` and `rules/<x>/`, with no edit to agent files.
**Acceptance**: `validate_kit.py --site <x>` passes; a pilot role runs end to end.

### US5 — See the department (P3)
An org chart and an animated 3D office show the roles, their job descriptions and the work flowing maker → checker → manager.
**Acceptance**: clicking a role shows its job description from `roles.json` content.

## Functional requirements
- **FR-001** Nine roles defined once in `config/roles.json`; one agent file per role.
- **FR-002** All ERP access read-only through the Cure MCP on a read-only DB user; onboarding is refused otherwise.
- **FR-003** All branches of the site every run; unreachable sources are reported, never substituted.
- **FR-004** Cancelled vouchers excluded everywhere.
- **FR-005** Makers hand off in the schema in `contracts/handoff.schema.json`.
- **FR-006** Chief Accountant spot-checks findings against the source and approves or returns (max two returns, then escalate).
- **FR-007** Internal Auditor sees outputs only, never workpapers.
- **FR-008** Site specifics only in site config; `validate_kit.py` rejects agent files containing site literals.
- **FR-009** Outputs only under `<hub_root>/Finance-Dept/runs/<period>/<role>/`.
- **FR-010** Staff-facing text in Arabic.
- **FR-011** The kit calls existing CFO-Cure / HR-Cure scripts where present and never modifies them.
- **FR-012** Plugin packaging is additive; existing packaged files stay byte-identical.

## Out of scope (v1)
Posting entries, approving payments, sending emails or bank files; live connection of the 3D page to run logs (v2); scheduling (v2, via n8n).

## Success criteria
- **SC-001** Pilot month: ≥ 90% of the AR accountant's findings confirmed by the human team; zero findings without evidence.
- **SC-002** A full-department run for one month completes in one session.
- **SC-003** Onboarding a second site needs no change to `agents/`.
