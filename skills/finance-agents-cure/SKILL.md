---
name: finance-agents-cure
description: Run or set up the AI finance department (finance manager, chief accountant, six role accountants, internal auditor) as Claude sub-agents on any EXSYS (Cure) ERP company, read-only via Cure MCP. Use for "شغّل الإدارة المالية", a monthly close review by the agent team, onboarding a new EXSYS site, or the department org chart / 3D office page.
---

# Finance-Agents-Cure — الإدارة المالية بالذكاء الاصطناعي

A simulated finance department of 9 agents that reviews an EXSYS (Cure) company's books, read-only, with maker/checker and an independent audit.
Spec: `specs/001-ai-finance-department/` · Principles: `.specify/memory/constitution.md` (read it first).

## Files
| Path | What |
|---|---|
| `config/model_policy.json` | default model per role, escalation and downshift rules |
| `config/roles.json` | the department: roles, reporting lines, job descriptions (single source) |
| `config/site.<site>.json` | site specifics: branches/DSNs, accounts, folders, rules_dir |
| `rules/<site>/*.md` | the site's standing review rules, one file per area |
| `agents/*.md` | the 9 sub-agent definitions (also packaged at the plugin root `agents/`) |
| `specs/001-ai-finance-department/contracts/handoff.schema.json` | the maker → checker handoff format |
| `templates/finance-office-3d.html` | org chart + animated 3D office page |
| `scripts/validate_kit.py` | consistency + portability checks |
| `scripts/build_desk_fin.py`, `scripts/desk_fin_include.py`, `templates/desk/fin-dept.src.js` | the Modeling Desk tab «الإدارة المالية» |
| `scripts/new_period.py` | creates `runs/<period>/` folders and the run log |

## Choosing the model for each agent (token budget)
Read `config/model_policy.json` before dispatching. For every Agent call pass `model` explicitly:
- start from the role's `default`; use `haiku` for the `task_overrides.haiku` kinds of task (single re-checks, referrals of one or two queries, housekeeping);
- move up to `opus` when one of the role's `up_to_opus_when` conditions holds, or when the agent returned `model_escalation` (one level up, once per role per period — ask the human before a second);
- chief accountant round-2 re-reviews of its own returned items run on `sonnet`;
- write the chosen model and the reason in `run_log.md`.
The user can override any choice in the request (e.g. «شغّل الضريبة على opus»).

## You are the Finance Manager's dispatcher (main session)
Sub-agents cannot start sub-agents, so the main session runs the department:

1. **Site.** Ask which site if more than one `config/site.*.json` exists; load it. Stop if `read_only_db_user_confirmed` is not `true`.
2. **Period.** Default = previous month (`YYYY-MM`). Run `python scripts/new_period.py --site <site> --period <YYYY-MM>`.
3. **Health check.** `cure_branch_status` — every branch in the site config must answer. Note any that don't.
4. **Makers (parallel).** Dispatch the requested accountants with the Agent tool (`subagent_type` = role id, e.g. `ai-reporting-hub:ar-insurance-accountant` when installed from the plugin). Prompt each with: site, period, kit path, hub_root, and the specific task if the user gave one. Default = all six.
5. **Checker.** For each `ready_for_review` handoff dispatch `chief-accountant`. Returned items go back to their maker (max two rounds).
6. **Audit.** After all approved/blocked, dispatch `internal-auditor` (independent — do not pass it workpapers).
7. **Consolidate.** Dispatch `finance-manager`; deliver `runs/<period>/finance-manager/summary.md` to the user in Arabic.
8. **Desk tab.** `python scripts/build_desk_fin.py --site <site>` → `Finance-Dept/desk/fin-dept.js` + `fin-office.html`; publish both BESIDE the Desk's index.html (publish_files, mode patch). index.html is not touched — it already loads `fin-dept.js` (if a Desk copy lacks the include, run `scripts/desk_fin_include.py <index.html>` before republishing it).
   Demo: `python scripts/build_desk_fin_demo.py --site <site>` → `Finance-Dept/desk/demo/` (company/branches renamed, money ×6.25, insurers keep real names, supplier names → «مورد ###», evidence narrations dropped; prints any leak). Copy both files beside the Demo Desk page and publish them with it.
   Self-contained copies: run `scripts/make_standalone.py <page.html>` on the local Desk / Demo page so a single copied file carries the tab (fin-dept.js and the 3D office are inlined); it lists any side file that is missing.
   Local copies (standing rule): also copy the published files to `Financial\` (live) and to `Demo\` + `Financial\Demo\` (demo), so the folders always match the live pages.
9. **Log.** Append each step to `runs/<period>/run_log.md` (time, role, status).

Single-role requests ("خلي محاسب الموردين يراجع أكتوبر") run steps 1–5 for that role only.

## Onboarding a new EXSYS site
1. Confirm a read-only Oracle user and a working Cure MCP for every branch.
2. Copy `config/site.example.json` → `config/site.<site>.json`; fill branches/DSNs, cost centres, accounts (discover with `cure_gl_accounts` on the main branch), folders.
3. Copy `rules/_template/` → `rules/<site>/`; write the site's standing rules (start from `rules/alfaihaa/` as a reference, keep only what the site confirms).
4. `python scripts/validate_kit.py --site <site>` must pass.
5. Pilot one role for one month (recommended: ar-insurance-accountant + chief-accountant), compare with the human team's result, then enable the rest.

## Never
Write to EXSYS · send email or bank files · hard-code a site's accounts in agents · edit the CFO-Cure / HR-Cure / RCM skills (call them, don't change them).
