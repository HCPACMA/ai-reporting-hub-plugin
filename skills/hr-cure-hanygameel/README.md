# HR-Cure Kit

Reusable kit behind the **HR Command Center** for Al Faihaa Group. It rebuilds the same page for another company that runs EXSYS (Cure). Start with `ADAPTATION_CHECKLIST.md` for a new company and `REFRESH_RUNBOOK.md` for a monthly refresh. `SPEC.md` is the full specification.

```
HR-Cure-Kit/
  SPEC.md                    specification, definitions, audit rules, traps
  SKILL.md                   Claude skill text (workflow)
  REFRESH_RUNBOOK.md         monthly refresh steps
  ADAPTATION_CHECKLIST.md    standing the kit up at a new company
  config/company.alfaihaa.json   company settings (copy and edit)
  config/playbook.json       calendar, checklist and best-practice text (English and Arabic)
  config/labels_ar.json      Arabic names for labels that come from Cure data
  data/payroll_notes.json    payroll notes register (English and Arabic), carried month to month
  sql/hr01a ... hr17         19 parameterised queries, each with its tie-out
  scripts/render_sql.py      fills placeholders (schema, dates, accounts, ID types)
  scripts/ingest.py          saved Cure replies -> extract JSON
  scripts/build_hr.py        extract + notes -> findings -> page, with gates
  scripts/notes_tool.py      list, close, reopen, add and apply notes (carry-over rule)
  templates/hr_command_center.template.html
  data/extract.alfaihaa.2026-10-12.json   the verified extract of the reference build
  raw_samples/               real tool replies, to see the input format
  tests/                     round-trip, gates, notes rule and browser smoke test (run_tests.py)
  docs/                      data dictionary, letters-review playbook, Al Faihaa baseline
```

Quick start (any machine with Python 3):

```
python3 scripts/render_sql.py --config config/company.<co>.json --asof YYYY-MM-DD --out sql_out/
# run each sql_out/hrNN_*.sql with cure_run_query, save the reply as raw/hrNN_*.txt
python3 scripts/ingest.py --raw raw/ --config config/company.<co>.json --asof YYYY-MM-DD --out data/extract.<co>.<date>.json
python3 scripts/build_hr.py --extract data/extract.<co>.<date>.json --config config/company.<co>.json --out out/
```

`out/HR_Command_Center.html` opens locally. `out/HR_Command_Center.artifact.html` is the fragment to publish with the Artifact tool, which adds the page skeleton itself.

The page has a left sidebar with sub tabs, Arabic (RTL), English or both, and a Payroll notes group whose open items move to the next month until closed. See `SPEC.md` section 5.

The page in the HR folder (`HR_Command_Center_2026-10-12.html`) is the Al Faihaa build from this kit.
