# Common rules — all roles (Al Faihaa)

- Cancelled vouchers (`STATUS = 'C'`) do not exist: exclude from every pull, balance and reconciliation. Posted (P) and open (O) both count.
- Balances are taken from ALL four branch databases (Riyadh, BUR1, BUR2, Rafha), never one branch.
- Discovery tools (`cure_list_tables`, `cure_find_tables`, `cure_describe_table`) only answer for Riyadh; discover there, then query the same bare table names on the other branches with `cure_run_query`.
- Riyadh needs the `EXSYS.` schema prefix; the other branches do not.
- `NOT IN` against a nullable column needs an explicit `IS NOT NULL` filter (Oracle returns zero rows otherwise).
- Cost centres: 000 head office, 001 Riyadh, 002 Buraydah 1, 003 Buraydah 2, 004 Rafha. G&A and other revenue belong to each branch; head office holds only expenses shared by all branches.
- Always refresh data (Cure + attachment folders of every branch) BEFORE any review. If a branch folder cannot be reached, say so — never review stale data.
- Every finding is provable: voucher no., amount, date and narration must be attached so a person can verify it.
- With every run, re-check earlier findings and mark each fixed / partly / still open.
- Copy-friendly output: voucher numbers in their own column.
- "Created in month X" = the voucher creation date in the voucher master tables (VOUCHER_MASTERS / CM_VOUCHER_MASTER), not the voucher date.
- Voucher-prefix → branch: see `voucher_prefix_branch` in the site config (e.g. BR2 = Buraydah 1, not Buraydah 2).

## Added after the 2026-10 run
- Every GL balance is the CONSOLIDATED balance of all four branches; a single-branch balance is shown only as detail.
- Referrals: an item for another role goes in `referrals` (to_role); each role reads referrals addressed to it in the same period and answers them.
- A finding that must be fixed before closing the month is marked `blocks_close: true`.
- Status `unverified` = an earlier finding that can no longer be located in the data; ask the human for the reference instead of marking it fixed.
