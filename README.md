# AI Reporting HUB plugin

Hany Gameel's AI Reporting HUB kits for EXSYS (Cure) ERP companies: CFO Modeling Desk (CFO-Cure), HR Command Center (HR-Cure), the AI finance and inventory department agents (Finance-Agents-Cure, Inventory-Agents-Cure) and the AI Reporting master playbook. Skills + code only; no company data.

Auto-synced nightly from `D:\Financial Management\Financial Report\AI Reporting HUB` (builder: `.plugin-sync/build_plugin.py`). Do not edit here; edit the kits on the PC.

## Skills
- `ai-reporting-by-hanygameel`
- `cfo-cure-hanygameel`
- `cure-theme`
- `finance-agents-cure`
- `hr-cure-hanygameel`
- `inventory-agents-cure`
- `inventory-audit-dashboard`
- `rcm` (NPHIES RCM Audit, maintained from the second account in `skills/rcm/`)

## Agents (AI finance + inventory departments)
- `ap-supplier-accountant`
- `ar-insurance-accountant`
- `chief-accountant`
- `cost-inventory-accountant`
- `finance-manager`
- `gl-accountant`
- `internal-auditor`
- `inv-auditor`
- `inv-controller`
- `inv-count`
- `inv-expiry`
- `inv-manager`
- `inv-planner`
- `inv-purchasing`
- `inv-receiving`
- `inv-valuation`
- `payroll-accountant`
- `vat-accountant`

## Commands
- `/ai-reporting-hub:cure-theme`
- `/ai-reporting-hub:refresh-cure`
  `refresh-cure [mcp-name] [all|desk|hr|inventory|finance]` fills every page from the Cure database (finds the Cure MCP by name or automatically) and applies the Cure colours.

## Install
- Claude Code: `/plugin marketplace add HCPACMA/ai-reporting-hub-plugin` then `/plugin install ai-reporting-hub@hanygameel-plugins`
- claude.ai: zip a skill folder and upload it under Settings > Capabilities > Skills.

## Excluded by design
Company data (data/, raw/, out/, cache/, exports), archives, and any file the builder's scan flags for national IDs, IBANs, phone numbers, emails or person names.
