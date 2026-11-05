# AI Reporting HUB plugin

Hany Gameel's AI Reporting HUB kits for EXSYS (Cure) ERP companies: CFO Modeling Desk (CFO-Cure), HR Command Center (HR-Cure) and the AI Reporting master playbook. Skills + code only; no company data.

Auto-synced nightly from `D:\Financial Management\Financial Report\AI Reporting HUB` (builder: `.plugin-sync/build_plugin.py`). Do not edit here; edit the kits on the PC.

## Skills
- `ai-reporting-by-hanygameel`
- `cfo-cure-hanygameel`
- `hr-cure-hanygameel`
- `rcm` (NPHIES RCM Audit, maintained from the second account in `skills/rcm/`)

## Install
- Claude Code: `/plugin marketplace add HCPACMA/ai-reporting-hub-plugin` then `/plugin install ai-reporting-hub@hanygameel-plugins`
- claude.ai: zip a skill folder and upload it under Settings > Capabilities > Skills.

## Excluded by design
Company data (data/, raw/, out/, cache/, exports), archives, and any file the builder's scan flags for national IDs, IBANs, phone numbers, emails or person names.
