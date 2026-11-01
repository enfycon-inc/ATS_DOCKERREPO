# Audit & Fixing Plan: Job Page Permission Error

## Executive Summary

The permission dialog on **All Jobs** and **My Jobs** is caused by the job filter drawer requesting the administrative user directory while the shared jobs page mounts. The dialog is accurate for the request (`/api/auth/users` returns 403), but that request is an implementation mistake: job filters need only people represented in jobs the current user is authorized to see. Account Managers, Recruiters, and BDMs should not receive `user:manage` merely to load job pages.

## Root Cause

- `ats_frontend_main/app/(dashboard)/job-posting/components/job-posting-dashboard.tsx:622` renders `FilterDrawer` for the shared jobs page.
- `ats_frontend_main/app/(dashboard)/job-posting/components/filter-drawer.tsx:54-63` loads filter data in a mount-time effect even while the drawer is closed. At line 61 it calls `atsApi.auth.listUsers()`.
- `ats_frontend_main/lib/ats-api.ts:578` sends that call to `/api/auth/users`.
- `ats_backend/src/auth/auth.controller.ts:246-258` rejects the request unless the caller has `user:manage` (or tenant-admin permissions). It throws the exact message shown in the screenshots: `Missing user management permission.`
- Default role definitions in `ats_backend/src/auth/services/auth-init.service.ts:185-187` grant `job:view` to Recruiter and Account Manager, but do not grant `user:manage`; BDMs using the Account Manager role therefore hit the same check. The jobs catalog itself has a separate `job:view` authorization at `ats_backend/src/jobs/jobs.controller.ts:44-51`.

The dialog appears during initial page load because the filter drawer's effect runs regardless of `isOpen`; its local `.catch(() => setUsers([]))` does not prevent the shared API error handler from showing a global permission dialog. The same shared component powers All Jobs and My Jobs.

There is a second use of the administrative directory in the same jobs page at `job-posting-dashboard.tsx:449-460`, used to translate a recruiter display name into an ID during an inline job update. It can produce the same error for these roles if that path is exercised.

## Impact Radius

- Affected: Account Manager, Recruiter, and BDM users opening All Jobs or My Jobs; any other `job:view` role without `user:manage` is also affected.
- Other job views using the shared dashboard may be affected by the same mount-time request.
- User administration must remain protected by `user:manage`; loosening `/api/auth/users` would expose broader staff directory data and is not an appropriate fix.
- No database migration is expected.

## Implementation Plan

1. Add job-filter option data to the existing authorized jobs catalog response (or use an equivalent job-scoped endpoint), returning only the minimal person fields required by the filters: stable user ID, display label, and filter category (job owner/account manager or assigned recruiter).
2. Build those options from the same tenant and job-visibility scope used by `findJobPage`; do not return the tenant-wide user directory. Keep the response limited to options relevant to jobs visible to the caller, and deduplicate results.
3. Update `FilterDrawer` to consume the job-scoped options, remove its `auth.listUsers()` call, and fetch options only when needed (drawer open or already supplied from catalog state). Keep existing user-management endpoint authorization unchanged.
4. Remove the remaining `auth.listUsers()` dependency in the jobs inline-update path. Resolve recruiter IDs from the job-scoped options or use the assignment's existing ID; preserve existing backend assignment/scope validation.
5. Add focused coverage for authorized job filter options and inaccessible tenant/branch/unit data, and verify that the three affected roles can open both pages without a user-management request.

## Edge Cases to Cover

1. A visible job has no account manager or no recruiter assignment: omit the missing person option while retaining the job's “unassigned” filter behavior.
2. A recruiter can see only assigned jobs: filter options must not reveal people attached exclusively to jobs outside that recruiter's visible scope.
3. A job references an inactive or deleted staff account: the option should remain safe and display a non-sensitive fallback label or be omitted without breaking job rows.
4. A large visible job set has duplicate owners/recruiters: return each option once and keep the catalog response bounded to minimal fields.

## Rollback Plan

Revert the jobs catalog option-contract and frontend consumer changes together. This restores current behavior for roles with user-management access; non-admin job viewers would again see the permission dialog. No data rollback is needed because no schema or records change.

## Approval Gate

No code has been changed. Await explicit approval before implementation.
