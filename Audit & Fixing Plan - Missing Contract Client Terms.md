# Audit & Fixing Plan

## Executive summary
The stored rate and the displayed label are separate from authorization. A confirmed backend branch returns `N/A` for numeric contract rates when the request lacks `job:bill_rate:view`, while allowing permanent commissions through `placement:view`. This produces the exact mixed display in the screenshot. The screenshot alone does not prove the affected account's effective permissions or the particular row's stored amount; live request/record inspection is required before changing authorization.

## Root cause and evidence
- `ats_backend/src/jobs/job-commercials.ts:63-81`: independently checks bill-rate and commission permissions. Numeric rates are returned only with `job:bill_rate:view`; otherwise it returns `N/A`.
- `ats_backend/src/jobs/jobs.service.ts:1671,1860`: list mapping passes request permissions into this formatter. The list query includes job fields (`:1369`).
- `ats_backend/src/auth/services/auth-init.service.ts:196-206`: initialization backfills the bill-rate capability only for existing system-role copies with `is_system = true`. Custom roles are deliberately outside this backfill.
- `ats_frontend_main/app/(dashboard)/job-posting/components/data-table/job-table-row.tsx:527-537`: renders the API value; renaming the column cannot restore a withheld rate.

## Implementation plan
1. Inspect the affected job's numeric bill fields and the signed-in account's effective active-role permissions through authorized read-only access. Compare the jobs API value with the table.
2. If the rate exists and permission is absent, use role administration to grant `job:bill_rate:view` to the intended role after confirming its scope; renew the session and verify. Preserve custom-role choices rather than automatically widening all roles.
3. If permission is present but the API still returns N/A, inspect deployed backend revision and actual query row before changing code. Local formatter supports numeric snake_case and camelCase fields.
4. If the job has no numeric rate, correct that job through its edit form; do not substitute candidate pay.
5. Keep the current single Client terms column and normalized schema. No new layout or preview is needed for this backend/data diagnosis.

## Impact radius and edge cases
Permission grants affect every accessible job for that role, within existing tenant/branch scope. Verify bill-only access without commission access, commission-only access without bill access, both permissions, missing rate, zero rate, and fixed/ranged monthly/hourly values. No extra per-row API calls or schema migration are proposed.

## Rollback plan
Remove only an explicitly approved role capability grant if needed, then renew the session. Retain existing role permissions and job data. Any later code correction must have an isolated diff and preserve backend field authorization.

# System Design Proposal

## Current architecture context
The API produces a permission-filtered client commercial string; the frontend displays it. Separate capabilities control numeric bill rates and placement commissions.

## Proposed solution
Retain this architecture. First distinguish missing stored data from missing effective capability using the affected request and job record. Apply a targeted configuration correction only when supported by that evidence. Do not infer financial access from job ownership or a role name.

## Security and performance audit
- Backend authorization remains authoritative; no frontend permission bypass.
- Tenant/branch job access remains enforced.
- No hardcoded account IDs or fallback rates.
- No additional list queries, per-row calls, or database fields.
- No application code, role configuration, or job data changed during this audit.
