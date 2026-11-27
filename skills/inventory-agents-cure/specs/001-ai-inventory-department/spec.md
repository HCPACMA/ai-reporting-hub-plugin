# Feature Specification: AI Inventory Department (إدارة المخازن بالذكاء الاصطناعي)

**Created**: 2026-11-21 · **Owner**: Hany Gameel · **Status**: Ready (no run yet)

## Summary
Nine Claude sub-agents that work like a structured inventory department on top of the Inventory Audit dashboard, read-only on EXSYS: Inventory Manager, Inventory Controller (checker), Controls & Fraud Auditor (independent), and six staff — receiving & issuing, cycle count & adjustments, expiry & slow-moving, demand & rebalancing, purchasing & vendors, stock valuation. Each has a job description, explicit duties by frequency, KPIs and the dashboard tabs it owns. Portable to any EXSYS company through the site config and rules folder.

## User stories
- **US1 (P1)** Monthly inventory review by the team, maker → checker → auditor → manager, one Arabic summary; stock-value items referred to the finance department.
- **US2 (P1)** One role on demand («خلي محلل الصلاحية يراجع نوفمبر»).
- **US3 (P1)** The Inventory Audit dashboard shows the department (live and demo): overview, **job duties per employee (sub-tab)**, findings and summary once runs exist, 3D warehouse.
- **US4 (P2)** New EXSYS site via site config + rules only.

## Requirements
- FR-001 roles.json is the single source (agents, dashboard tab, 3D page).
- FR-002 Read-only; no posting, adjusting, ordering or transferring.
- FR-003 Every finding has document no., item code, store, date, quantity, value.
- FR-004 Purchase invoices with returns excluded from price analyses; slow-moving needs ~3 months history.
- FR-005 Dashboard additions are side files + one include; capabilities and db collections untouched; demo never shows the company name or real numbers.
- FR-006 Local copies saved and self-contained after every publish.
