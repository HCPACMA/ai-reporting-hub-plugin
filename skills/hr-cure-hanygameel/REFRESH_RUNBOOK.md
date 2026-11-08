# HR Command Center: refresh runbook

Run after each payroll close (the draft month is detected automatically). About 18 short calls, none heavy.

1. `python3 scripts/render_sql.py --config config/company.alfaihaa.json --asof <today> --out sql_out/`
2. Send each `sql_out/hr*.sql` to `cure_run_query` with `branch = Riyadh` (the database that holds payroll). Independent jobs can run together. Save each reply as `raw/<job-name>.txt` (the file name is the SQL file name without `.sql`).
3. `python3 scripts/ingest.py --raw raw/ --config config/company.alfaihaa.json --asof <today> --out data/extract.alfaihaa.<date>.json`. It stops if a job file is missing.
4. Update the payroll notes first (see Monthly payroll notes below), then `python3 scripts/build_hr.py --extract data/extract.alfaihaa.<date>.json --config config/company.alfaihaa.json --out out/`. Exit code 2 means a gate failed; read `out/build.md`, fix the cause, do not publish.
5. Compare with the previous build: headcount, last-month gross, GL provisions, number of flags. Explain every change above 5 percent before publishing.
6. Run `python3 tests/run_tests.py`, then open `out/HR_Command_Center.html` at 1280 px and 400 px in light and dark, switch Arabic, English and both, click every page, check the console. A blocked Google font in a sandbox is not an error.
7. Publish `out/HR_Command_Center.artifact.html` with the Artifact tool to the same URL. Copy `out/HR_Command_Center.html` to the HR folder as `HR_Command_Center_<date>.html`. Keep the extract in `data/`.
8. Update the project doc `claude/hr-command-center-artifact.md` with the date, key figures, flags opened and closed.

If Cure is unreachable or a job cannot finish, stop and report. Never publish a partly refreshed page.

## Monthly payroll notes

1. `python3 scripts/notes_tool.py list --month <YYYY-MM>` shows what the new month starts with: everything still open from earlier months is carried automatically.
2. Close what was fixed in Cure: `python3 scripts/notes_tool.py close A01 A02 --month <YYYY-MM>`. Close only after the correction is visible in Cure.
3. If someone closed or added notes in the published page, paste its Export box into a file and run `python3 scripts/notes_tool.py apply changes.json`.
4. Add the new month's findings (from the letters review) with `notes_tool.py add ...`, English and Arabic. Rebuild and republish.

## Monthly letters review

After the build, run the letters review (`docs/LETTERS_REVIEW_PLAYBOOK.md`) and re-check the future-month tracker for letters whose month has arrived.

## Known open decisions

Names of leave type codes 09 and 17 · whether to move leavers to the recorded separation date once HR fills it · a scheduled monthly refresh (not created; needs approval).

## Cure skin (7 Nov 2026)
The template now carries the Cure skin block (see _theme/cure/README.md). Keep it when editing the template; to change the look edit _theme/cure and run apply_cure_skin.py hr on the template.
