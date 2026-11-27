# Changelog

## 1.3.0 — 2026-11-21
- Modeling Desk tab «الإدارة المالية · AI Agents» (new sidebar group): overview KPIs, close blockers, staff status with model used, 68 findings with filters and evidence (copy voucher no.), management summary, internal audit, run log, embedded 3D office. Built by `scripts/build_desk_fin.py` from `Finance-Dept/runs/`, published as `fin-dept.js` + `fin-office.html` beside the Desk page; index.html only gains one include (`scripts/desk_fin_include.py`).
- Demo: `scripts/build_desk_fin_demo.py` (CFO-Cure demo kit v180 rules + supplier-name masking + leak check); Demo Desk now carries the tab.
- 3D office: auto-fit, camera buttons (zoom, rotate, tilt, pan, fit, full screen), Ctrl+wheel zoom so the page scroll never sticks; vertical swipe scrolls on phones.

## 1.2.0 — 2026-11-21
- Model policy per role (`config/model_policy.json`): makers/auditor/manager on sonnet, chief accountant on opus, haiku for single re-checks and housekeeping; escalation rules per role.
- Agents carry `model:` in frontmatter and can request a stronger model via `model_escalation` in the handoff (schema).
- SKILL.md: dispatcher passes the model on every Agent call and logs the choice.

## 1.1.1 — 2026-11-21
- 3D office restyled as a modern office: concrete floor, walnut slat wall, black-framed glass, linear pendant lights, bench desks (wood top, steel frame, drawer pedestal) facing each other across a planter, black mesh chairs, silver monitors.

## 1.1.0 — 2026-11-20 (after the first full-department run, 2026-10)
- Schema: `referrals` (between roles, answered by the receiver), `blocks_close` on findings, status `unverified`.
- All makers: answer referrals, mark close blockers, consolidated balances always.
- Chief accountant: unanswered referrals are a return reason; list close blockers on approval.
- Internal auditor: reads the review decision only, not review notes; checks referrals were answered.
- Rules: AP default credit terms → on hold, DRAFT bank file, non-cash reductions, prior approval by code; VAT ZATCA status fields + all open months + closing-JV lines on non-VAT accounts + invoice-type check; payroll commission-accrual timing + day-31 wording; GL bank 1224005 pattern; cost data gaps, status-T cost, UoM errors.
- Site config: prior-approval suppliers by code, default credit-term codes.

## 1.0.2 — 2026-11-19
- Al Faihaa accounts confirmed from the chart of accounts (all 4 branches): suppliers, VAT input / output / settlement.
- VAT rules: monthly closing into settlement, payment from settlement, return↔TB method from CFO-Cure SPEC §3.

## 1.0.1 — 2026-11-19 (after the 2026-10 AR pilot)
- AR rules: deduct credit notes / rejection closings with their VAT line; explicit pro-rata-on-remaining formula; check sibling sub-accounts before an overpayment finding.
- Common rules + site config: `voucher_prefix_branch`, `voucher_created_date_source`.
- Handoff schema: draft-07 (works with jsonschema 3.x); new `scope_notes_ar`.
- All maker agents: scope limits go in `scope_notes_ar`.

## 1.0.0 — 2026-11-19
- New kit: constitution, spec-kit docs (001-ai-finance-department), roles registry (9 roles), handoff contract.
- Agents: finance-manager, chief-accountant, internal-auditor, ar-insurance, ap-supplier, vat, payroll, cost-inventory, gl.
- Site config (example + alfaihaa) and site rules (template + alfaihaa, 7 areas).
- Scripts: validate_kit.py, new_period.py, check_build_diff.py.
- Template: finance-office-3d.html (org chart + animated 3D office).
- Plugin build: kit added as a third source; agents packaged at plugin root; existing files unchanged.
