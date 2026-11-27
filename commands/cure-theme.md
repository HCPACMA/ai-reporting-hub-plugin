---
description: Apply the Cure (EXSYS) colours and top bar to an AI Reporting HUB page (Desk, HR or Inventory) so it looks the same on any computer.
argument-hint: "<desk|hr|inv> <page.html> [more pages…]"
---

# /cure-theme — ألوان Cure

Arguments: `$ARGUMENTS`

1. Copy `${CLAUDE_PLUGIN_ROOT}/skills/cure-theme/` to a writable folder. If `snippet_desk.html`, `snippet_hr.html` or `snippet_inv.html` is missing there, run `python3 build.py` in it.
2. For each page: `python3 apply_cure_skin.py <desk|hr|inv> <page.html>` (idempotent: replaces the block between `<!--CURE-SKIN:start` and `<!--CURE-SKIN:end -->`, or inserts it).
3. If the page is a published artifact, republish it to the same URL. Do not change data, filters or calculations.
4. Colours: Cure blue `#0B6FBF`, white surfaces, Roboto/Cairo, navy in dark mode (see `README.md` there). To change the look, edit `base.css` / `app_*.css`, run `build.py`, then apply again.
