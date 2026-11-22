---
name: "rcm-cure-hanygameel"
description: "Deploy, refresh or demo Hany Gameel's NPHIES RCM dashboard (dashboard, audit + appeal workbooks, anonymised Demo, daily refresh) at any hospital or clinic on EXSYS / Cure+."
---

# RCM Cure+ deployment (Hany Gameel kit)

Stand up the same RCM dashboard, workbooks, Demo and daily refresh at a new EXSYS/Cure+ facility, or refresh an existing one. All logic lives in the **RCM Cure Kit**. This skill tells you where to get it, the order to run it in and the traps to avoid.

## Non-negotiable rules
- **Read-only.** Send only `SELECT`/`WITH` through the facility DB connector's `*_run_query`, and never modify EXSYS.
- **SQL guard.** Never schema-qualify tables (the guard blocks `SYS.`). Never use `DBMS_` or `TRUNCATE` (no `DBMS_LOB`, no `LISTAGG … ON OVERFLOW TRUNCATE`). Use `INSTR`/`SUBSTR` on CLOBs and cap `LISTAGG` with `ROWNUM<=n`.
- **What to display.** Show the source as **"Cure+"** only. Never show a host, IP, DSN or schema, even though `*_server_info` reveals them.
- **No invented rows.** A missing pull means the tab shows its empty state. The CHI modules in `build_chi.py` are illustrative and are labelled as such.
- **Appeals.** Appeals are prepared in the workbook and keyed by facility staff. Never send anything to NPHIES or a payer.
- **Demo.** Only the leak-scanned Demo may leave the facility. Each facility gets its own artifact, folder and scheduled task.

## Step 1: Get the kit
Try these sources in order:
1. **The connected facility folder.** If `RCM_Cure_Kit.zip` is there (`device_list_dir`), stage it with `device_stage_files` and `rm -rf /tmp/rcm && unzip -oq RCM_Cure_Kit.zip -d /tmp && mv /tmp/RCM_Cure_Kit /tmp/rcm`.
2. **The hosted kit** at `https://claude.ai/artifact/Rvjt3Jwgoxd6uLUW7YTq5U`.
   - Run `Artifact action:"list" scope:"files" url:<that>` to get every path.
   - Run `Artifact action:"read" url:<that> paths:[…all…] out_dir:"/tmp/rcm"`.
   - The constitution is published as `specify/memory/constitution.md` (no leading dot).
3. **Neither.** Ask the user to attach `RCM_Cure_Kit.zip`. The reference copy is in their `NPHIES RCM Audit` folder.

Then read `specs/001-rcm-cure-deployment/tasks.md`. It holds the 30 numbered tasks (T-01…T-30) with an acceptance check for each. Also read `plan.md` §6, which lists the site-adaptation points. Follow tasks.md. The steps below are the condensed path plus the traps it doesn't spell out.

## Step 2: Connect and profile (T-04 → T-10)
1. **Find the facility's DB tools.** Run `ToolSearch "+<Server> run_query server_info"`. They are named `mcp__remote-devices__<Server>__<server>_run_query`. Call `*_server_info`. If the call fails, the desktop bridge is offline: stop and tell the user.
2. **Preflight.** Run `tools/preflight_tables.sql`, where 26 objects are expected. Then run each block of `tools/preflight_profile.sql` **separately**.
3. **Fill `site_config.json`** from `site_config.example.json`:
   - Names: `facility_en`, `facility_ar`, `short_name` (the word the Demo scrubs) and `mcp_server`.
   - `org_no` from preflight 2a. If there is more than one org, add an org filter to queries 01-17, 24 and 28 and log it in `DEVIATIONS.md`.
   - `cash_group_label` from 2b.
   - `code_prefix_remap` from 2c, only if the product families differ from 11 med / 40 inj / 55 lab / 95 img / 85 vaccine.
   - `outpatient_only` from 2f. The facility is outpatient when there is no `ADMISSION_NO`.
4. **Render the queries.** Run `python3 tools/render_queries.py site_config.json`. It writes `queries/rendered/*.sql` and `queries/RUN_PLAN.md`.
5. **Smoke-test.** Run every rendered query with `max_rows:1`. On ORA-00904, map the column with `*_describe_object`, fix both the rendered file and the template, and log it in `DEVIATIONS.md`.

## Step 3: Pull (T-11 → T-18)
- **Build folder.** `mkdir -p /tmp/rcm/run/raw && cp /tmp/rcm/src/* /tmp/rcm/site_config.json /tmp/rcm/run/ && cp /tmp/rcm/reference/sfda_ref.json /tmp/rcm/run/raw/`
- **Run order.** Follow RUN_PLAN.md row by row with `max_rows:1000`, and save each result to `run/<raw target>`.
- **Paged rows.** Repeat the same SQL, changing only the OFFSET (a literal or `binds {"off":n}`), with 0, 1000, 2000… until a page is empty.
  - DXAPPR_EP is heavy. Run it sequentially, or at most 3 pages in parallel.
- **Large results** are auto-saved by the harness to a tool-results file. Stage them with `python3 tools/stage_result.py <saved_file> run/raw/<name>.md`.
- **Small results** come back inline. Stage them with `python3 tools/grab_inline.py "<distinctive header cells>" run/raw/<name>.md`. Never retype rows.
- **No hand-made CSVs.** Save DXCATALOG as `raw/drug_catalog.md` and SFDA_SERVICES pages as `raw/services_pNN.md`. `prep_raw.py` builds the CSVs and `raw/agg.json` itself.
- **Check inputs.** Run `cd run && python3 ../tools/check_raw.py`. Required inputs must be OK. Optional gaps just leave tabs empty.

## Step 4: Build and verify (T-19 → T-23)
- **Build.** Run `python3 rcm_refresh.py`. It rebuilds every JSON file, `NPHIES_RCM_Audit.xlsx`, `NPHIES_Appeal_Batch.xlsx` and `rcm_dashboard.html`.
- **Recalculate the appeal workbook** with the xlsx skill's `recalc.py`. It must report 0 errors.
- **Reconcile.** Each Overview KPI must equal its raw pull's row count.
- **Browser check.** In Playwright at 1920 px and 1366 px, call `show(id)` for every id in `SEC_IDS`. There must be 0 page errors and `scrollWidth` must equal the viewport width.
- **Demo.** Run `python3 build_demo.py && cp demo/rcm_dashboard.html demo/rcm_demo.html && python3 ../tools/leak_scan.py demo/rcm_demo.html`. Publish the Demo only if the scan exits 0.

## Step 5: Publish and schedule (T-24 → T-30)
1. **Publish the dashboard.** First publish: `Artifact file_path=run/rcm_dashboard.html icon="chart"`. Save the URL to `site_config.json.artifact_url`. For later refreshes, read the artifact, then republish with `url=`.
2. **Publish the Demo** from `run/demo/rcm_demo.html` (its title is "Demo"). Save the URL as `demo_artifact_url`.
3. **Deliver files.** `SendUserFile` the dashboard, both workbooks, the Demo, `site_config.json` and `DEVIATIONS.md`. Then `device_commit_files` them into the facility folder, including `RCM_Cure_Kit.zip` so the daily task can stage it.
4. **Schedule the daily refresh.**
   - Run `python3 tools/render_prompt.py run/site_config.json`.
   - Call `create_trigger` with the rendered `prompts/daily_refresh.<short>.txt` and `requires_local_device=true`. The cron is in UTC: 03:00 Riyadh is `0 0 * * *`.
   - Tell the user it needs their approval.
5. **Record the deployment.** Write the project doc `claude/RCM_Deploy_<Facility>.md` with the config, preflight answers, deviations, URLs and first-run headline numbers.
6. **Tell the user** that artifacts are private until shared from the Share menu.

## Refresh-only requests
For an existing facility, stage `site_config.json` and the kit from the facility folder, then run Step 3 → Step 4. Republish to the saved URLs.

## Known traps (found in the v1.0 drill)
- **ORA-00937.** Oracle raises it when a scalar subquery (`(SELECT … FROM DUAL)`) is mixed with aggregates. Use a constant expression, or wrap everything in `SELECT … FROM DUAL`.
- **No `EPISODE_TYPE` column** in `RC_PATIENT_EPISODES`. Detect inpatients with `ADMISSION_NO`/`ADMITTED_FLAG`.
- **Missing `site_config.json`.** Without it next to the scripts, the header reads "Unconfigured Facility". Always copy it into `run/`.
- **Vitals sent to NPHIES.** Cure+ sends the **first** vitals reading of a visit. The temperature carried in the bundle is read at `INSTR(API_SEND_RESPONSE,'"temperature"')+42`, so verify the offset on one claim at a new site.
- **Customer-group numbers are site-specific.** For example, Bupa was group 6 at the reference site. Never hard-code them; always join to `CUSTOMER_GROUPS.DESCRIPTION_P`.