---
name: inventory-agents-cure
description: Run or set up the AI inventory department (inventory manager, controller, controls & fraud auditor, six inventory staff) as Claude sub-agents on any EXSYS (Cure) company, read-only via Cure MCP, built on the Inventory Audit dashboard. Use for «شغّل إدارة المخازن», a monthly inventory review by the agent team, the inventory org chart / job duties / 3D warehouse, or onboarding a new EXSYS site.
---

# Inventory-Agents-Cure — إدارة المخازن بالذكاء الاصطناعي

Same operating model as Finance-Agents-Cure (read `.specify/memory/constitution.md` first): makers → Inventory Controller (checker) → Controls & Fraud Auditor (independent) → Inventory Manager (consolidates) → referrals to the finance department where money is involved.

## Files
| Path | What |
|---|---|
| `config/roles.json` | 9 roles: job description, responsibilities, **duties** (frequency · task · dashboard tab · output), KPIs, owned dashboard tabs |
| `config/model_policy.json` | default model per role (controller opus, others sonnet, haiku for single re-checks) and escalation |
| `config/site.<site>.json` | inventory DB branch, tables, folders, dashboard slugs and capabilities |
| `rules/<site>/inventory.md` | standing inventory rules |
| `agents/*.md` | sub-agents (also at the plugin root `agents/`, prefixed `inv-`) |
| `templates/warehouse-3d.html` | 3D warehouse + org chart + job descriptions |
| `templates/tab/inv-dept.src.js` | Inventory Audit dashboard tab «إدارة المخازن · AI Agents» (overview · job duties sub-tab · findings · summary · 3D) |
| `scripts/build_inv_tab.py` | builds `Inventory-Dept/desk/inv-dept.js` (+ demo) and `inv-office.html` |

## Dispatch (main session = the inventory manager's dispatcher)
1. Load site config; stop unless `read_only_db_user_confirmed`. Period default = previous month; `python scripts/new_period.py --site <site> --period <YYYY-MM>`.
2. `cure_branch_status` — the inventory database branch must answer.
3. Makers in parallel (`subagent_type` = role id, `model` per `config/model_policy.json`): inv-receiving, inv-count, inv-expiry, inv-planner, inv-purchasing, inv-valuation.
4. inv-controller reviews each handoff (max two returns, then escalate to inv-manager).
5. inv-auditor (independent), then inv-manager consolidates → `runs/<period>/inv-manager/summary.md`.
6. Dashboard tab: `python scripts/build_inv_tab.py --site <site>` → publish `inv-dept.js` + `inv-office.html` beside the dashboard index.html (patch), live and demo; save the same files locally and make the local pages self-contained (Finance-Agents-Kit `scripts/make_standalone.py`).
7. Log every step and model choice in `runs/<period>/run_log.md`.

## Never
Write to EXSYS · run `refresh_dashboard_json.py` · drop the dashboard's capabilities or db review collections · put the company name or real numbers in a demo.
