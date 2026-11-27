# Data model

## Role (`config/roles.json` → `roles[]`)
| field | type | note |
|---|---|---|
| id | string | kebab-case; equals agent file name and agent `name` |
| name_ar / name_en | string | |
| reports_to | role id \| `board` | |
| kind | orchestrator \| checker \| maker \| independent | |
| color | hex | org chart / 3D office |
| summary_ar, responsibilities_ar[] | Arabic | the job description |
| site_keys[] | config paths the role needs | missing → role reports `blocked` |
| uses[] | skills/scripts it may call | |
| outputs[] | paths under runs/<period>/ | |
| cadence | string | |

## Site (`config/site.<x>.json`)
branches[] (key, dsn, schema_prefix, cost_centre, name_ar) · cost_centres · cancelled_status · accounts{} · nphies_branches[] · inventory · vat · folders{} · rules_dir · suppliers_prior_approval[] · read_only_db_user_confirmed.

## Handoff (`contracts/handoff.schema.json`)
role, period, site, task, data_as_of, branches_covered[], branches_missing[], summary_ar, totals{}, findings[] (id, severity, title_ar, detail_ar, amount, rule, evidence[], status), files[], status, review{decision, notes_ar[], reviewed_at}.

## Run folder
`<hub_root>/Finance-Dept/runs/<YYYY-MM>/` → `run_log.md` + one folder per role.

## Finding lifecycle
`new` → (next run) `still_open` | `partly_fixed` | `fixed`. Ids are stable: `<role>-<area>-<key>` e.g. `ar-pay-BR1-26-00195`.
