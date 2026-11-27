# Quickstart

## Al Faihaa (already configured)
```
python Finance-Agents-Kit/scripts/validate_kit.py --site alfaihaa
```
Then in Claude: «شغّل الإدارة المالية لشهر 2026-10» — or one role: «خلي محاسب الذمم المدينة يراجع أكتوبر».

## New EXSYS company
1. Cure MCP connected for every branch, on a read-only DB user.
2. `config/site.example.json` → `config/site.<x>.json` (fill branches, accounts, folders; set `read_only_db_user_confirmed: true`).
3. `rules/_template/` → `rules/<x>/`; write the site's rules.
4. `python scripts/validate_kit.py --site <x>`.
5. Pilot: AR accountant + chief accountant for one month.

## Pages
`templates/finance-office-3d.html` — open in a browser or publish as an artifact.
