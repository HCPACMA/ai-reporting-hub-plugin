---
description: Refresh the numbers on every AI Reporting HUB page (CFO Desk, HR, Inventory, AI Finance/Inventory tabs) from the Cure (EXSYS) database through the Cure MCP, apply the Cure colours, and republish the artifacts.
argument-hint: "[mcp-name] [all|desk|hr|inventory|finance] [--asof YYYY-MM-DD]"
---

# /refresh-cure — تحديث كل الصفحات من قاعدة بيانات Cure

Arguments: `$ARGUMENTS`
- 1st word (optional): the **MCP server name** that exposes `cure_run_query` (for example `Cure_MCP`, `CureDB`, `exsys`). Omit it to auto-detect.
- 2nd word (optional): which pages — `all` (default), `desk`, `hr`, `inventory`, `finance`. Several can be given separated by commas.
- `--asof` (optional): the as-of date; default is today.

Reply to the user in the language they write in (Arabic by default). Keep a task list: one item per page plus a final "check" item.

## 0. Find the Cure MCP (by name or automatically)
1. If an MCP name was given, search the tools with ToolSearch for `+<name> cure_run_query` and use the server whose tool name ends in `__cure_run_query` and contains that name (case does not matter).
2. If no name was given, ToolSearch `cure_run_query` (and `cure_branch_status`). Collect every server that exposes `cure_run_query`:
   - exactly one → use it;
   - more than one → ask the user which one (list the server names);
   - none → stop and tell the user: "No Cure MCP is connected. Connect the Cure MCP (or give its name: `/ai-reporting-hub:refresh-cure <mcp-name>`)." Do not use any other data source.
3. Smoke test: `cure_branch_status` (or `SELECT 1 FROM DUAL` with `cure_run_query`) for every branch. Note which branches answer. If none answers, stop and report "Cure is offline"; never publish.
4. Everywhere the kit docs say `cure_run_query` / `Cure_MCP`, use the tool of the server found here. Save the choice in `cure_mcp.json` (`{"server": "<name>", "branches": [...], "checked": "<date>"}`) in the work folder so later runs reuse it.

## 1. Check that the site matches the kit settings
The kits ship tuned to Al Faihaa: four branch databases `01 Riyadh (schema EXSYS.)`, `02 BUR1`, `03 BUR2`, `04 Rafha` (`CFO-Cure-Kit/refresh/refresh.py` → `BR`), and HR settings in `hr-cure-hanygameel/config/company.alfaihaa.json`.
- If the branches the MCP reports are the same → continue.
- If they differ (another company or other branches) → do not guess. For the Desk, edit `BR`/`YFILE`/`EXPC`/`CCBR` in a work copy of `refresh.py` with the user; for HR copy the config to `company.<site>.json` and follow `docs/ADAPTATION_CHECKLIST.md`. Ask the user to confirm the mapping before running any page.

## 2. Work folder
The plugin folder is read-only: copy the kits from `${CLAUDE_PLUGIN_ROOT}/skills/` to a work folder (cloud: `/home/claude/work/kits/`; the user's PC: the HUB folder if it is connected). Set `CFO_ROOT=/home/claude/work`.
If the user's PC is connected and has `CFO-Cure-Kit\cache\cfo_cache_latest.tgz`, stage it and `refresh.py restore` it after `setup` (incremental run). Otherwise this is a **new install**: a full first read (step 3a).

## 3. Refresh each page (only the pages asked for)
Run SQL only through the Cure MCP found in step 0, SELECT only. Independent branch calls run in parallel (4 at a time); heavy jobs one at a time. If a call times out, wait 3 minutes and retry with a shorter date range. Parse results from the saved result files, never retype numbers.

a. **desk — CFO Modeling Desk** (`cfo-cure-hanygameel`, runbook `refresh/README.md`):
   `python3 refresh.py setup`. **New install** (no `$CFO_ROOT/AlFaihaa_Modeling_Desk.html`): copy `templates/ModelingDesk_shell.html` there first — it is the live Desk's layout (sidebar, languages, Cure skin) with dummy numbers and a banner. Then find the first year with postings (`SELECT MIN(VM_DATE) FROM <P>GL_TRANSACTIONS_DETAILS` per branch) and run `BOOT_LEDGER=<year>-01-01 BOOT_INV=<year>-01-01 python3 refresh.py plan --weekly`; otherwise `python3 refresh.py plan` →
   run every job in `runs/<id>/plan.md` → `refresh.py ingest …` per result → `refresh.py status` until nothing is missing → `refresh.py build` → read `runs/<id>/build.md` (the build re-applies the Cure skin).
   Payloads the kit has no job for (see the refresh docs: AR, suppliers, NPHIES, peers…) keep dummy numbers: list them to the user and keep the banner until they are filled. Remove the `<!--SHELL-BANNER:start-->…<!--SHELL-BANNER:end-->` block only when every gate passed and no payload is still a dummy.
   Then the AI Finance tab: `finance-agents-cure/scripts/build_desk_fin.py` (see that SKILL.md) and `desk_fin_include.py <page>`.
b. **hr — HR Command Center** (`hr-cure-hanygameel`, `REFRESH_RUNBOOK.md`): `render_sql.py` → run each `sql_out/hr*.sql` on the HR branch → `ingest.py` → `build_hr.py` (template `templates/hr_command_center.template.html`, already carries the Cure skin) → `tests/run_tests.py`. `templates/hr_live_shell.html` is the live page with dummy data — a layout reference only, never published.
c. **inventory — Inventory Analysis & Audit** (`inventory-audit-dashboard`, `REFRESH_RUNBOOK.md` Level B on a new install, Level A otherwise). Start from `inventory-agents-cure/templates/inventory_audit_shell.html` when there is no dashboard yet; re-embed only the rebuilt keys of `<script id="audit-data">`; then `apply_cure_skin.py inv <page>` and the AI Inventory tab (`inventory-agents-cure/scripts/build_inv_tab.py`). Remove the `<!--SHELL-BANNER:start-->…<!--SHELL-BANNER:end-->` block only after the verify step passes.
d. **finance — AI Finance Department** (`finance-agents-cure/SKILL.md`): new period, agents' runs, `build_desk_fin.py`.

## 4. Colours (Cure skin) on every page
Before publishing, run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/cure-theme/apply_cure_skin.py <desk|hr|inv> <page.html>` (idempotent). If the snippets are missing, run `build.py` in the same folder first. A page published without the `<!--CURE-SKIN:start` block is a defect.

## 5. Publish and report
- Publish each page with the Artifact tool. If the user already has that page among their artifacts (`list`), update the same URL; otherwise create it. Keep the side files (`fin-dept.js`, `fin-office.html`, `inv-dept.js`, `inv-office.html`, `cure-skin-*.js`) beside index.html. Restate the inventory dashboard's capabilities (see its runbook).
- Never publish a page whose build gates failed, whose refresh is partial, or that still has the sample banner. Say which page was held back and why.
- On the user's PC (if connected) save local copies as the kit READMEs say, and `refresh.py pack` the Desk cache back to `CFO-Cure-Kit\cache\cfo_cache_latest.tgz`.
- Final reply: a short table — page · as-of date · status (updated / held back + reason) · key figure that changed most.
