# Research notes

1. **Orchestration** — Claude Code sub-agents cannot spawn sub-agents. Decision: the main session (following SKILL.md) is the Finance Manager's dispatcher; the `finance-manager` agent only consolidates.
2. **Packaging agents in a plugin** — a plugin's root `agents/` folder is auto-discovered; installed agents are addressed as `<plugin>:<agent>` (here `ai-reporting-hub:<role>`). Decision: ship agents at the plugin root, keep the source copy in the kit.
3. **Tool lists** — MCP tool names depend on the server name at each site, so agent frontmatter does not pin tools (inherits the session's). The read-only guarantee is the DB user, gated by `read_only_db_user_confirmed`.
4. **Independence** — the auditor is given outputs only; it re-queries Cure itself rather than reusing makers' SQL.
5. **Portability** — every site literal (accounts, branches, folders) moved to `site.<x>.json`; `validate_kit.py` fails if an agent file contains one.
6. **Do-not-break** — the existing builder packages CFO-Cure, HR-Cure and the master playbook, and the push script protects `skills/rcm/`. The new kit is a third source; `.html` is allowed only for this kit's `templates/` so other kits' HTML (which may contain data) is never picked up.
