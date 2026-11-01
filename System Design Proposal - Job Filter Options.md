# System Design Proposal: Permission-Safe Job Filter Options

## Current Architecture Context

The shared job dashboard loads its filter drawer on mount. The drawer calls the general `/api/auth/users` directory endpoint to build account manager and recruiter filters. That endpoint correctly requires `user:manage`, while standard job viewers only have `job:view`. The result is a 403 and a global permission dialog on All Jobs and My Jobs.

The existing jobs catalog endpoint is already protected by `job:view` and computes aggregate options from the caller's scoped job query. It is the suitable source for job-related filter values, with a small response-contract extension to include IDs alongside labels.

## Proposed Solution

- Extend job catalog filter options with deduplicated account-manager and recruiter `{id, label}` values derived only from jobs visible to that actor. Keep the existing tenant, branch, business-unit, and job visibility predicates as the source of truth.
- Have the job filter drawer consume those options or fetch a dedicated, batched job-filter-options response guarded by `job:view`. Do not call the administrative user directory.
- Keep `/api/auth/users` and its `user:manage` guard unchanged.
- Remove the inline recruiter-name-to-ID lookup through `auth.listUsers()` in the jobs dashboard; use the job-scoped option data or assignment IDs already present, while retaining backend assignment validation.
- No schema or migration change.

## Security & Performance Audit

- **Tenant isolation:** derive IDs and labels through the scoped jobs query and same tenant ID; never query a tenant-wide user list for job filters.
- **Authorization:** require `job:view` for the filter options and preserve all existing job visibility and assignment rules. Do not grant user-administration permission to job roles.
- **Data minimization:** return only the ID and display label needed by filters, not email, status, profile, or user-management fields.
- **Performance:** batch options with the catalog response (or one request), deduplicate in SQL, and avoid a second full user-directory fetch on page load.
- **Contract integrity:** type the added catalog option fields in the frontend/backend contract and cover their shape in focused tests.

## Approval Gate

This is a backend and frontend behavior change, but it requires no UI redesign, schema change, or migration. No implementation has started pending approval.
