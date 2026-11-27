# Cure skin (v1, 7 Nov 2026)
Makes the CFO Modeling Desk, HR Command Center and Inventory Audit look like part of Cure (EXSYS):
Cure blue (#0B6FBF) + white surfaces, Roboto/Cairo, a Cure-style top bar (logo, breadcrumb
Administrative > module > group > screen, screen search with Ctrl+K, print, back-to-top, user/date),
a footer strip with the Al Faihaa name, card-style sidebar items with icon boxes (active = solid blue),
and blue table header bars. Data, filters and calculations are untouched; dark mode keeps a navy version.

Files: base.css / base.js (shared) + app_desk.css / app_hr.css / app_inv.css (per page)
-> `python3 build.py` makes snippet_<desk|hr|inv>.html -> `python3 apply_cure_skin.py <desk|hr|inv> <page.html>`
(idempotent: replaces the block between <!--CURE-SKIN:start--> and <!--CURE-SKIN:end -->).

Wired in:
- CFO: refresh.py `build` re-applies CFO-Cure-Kit/templates/cure_skin.html on every build.
- HR: the block is inside HR-Cure-Kit/templates/hr_command_center.template.html, so every build carries it.
- Inventory: after apply_vNN.py run `apply_cure_skin.py inv <dashboard.html>` before publishing (alfaihaa/cure_skin.html).
Backups of every file changed: *.pre_cure.html (refresh.pre_cure.py, template .html.pre_cure).
