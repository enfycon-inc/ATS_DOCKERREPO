# Unit Admin sidebar, office context, and canonical tenant role

## Symptom and cause

The screenshot showed a Unit Admin label, tenant dashboard/navigation, and a persisted Assigned Office placeholder. Investigation confirmed role-based navigation grants, fabricated permission defaults (including for empty arrays), ambiguous display-name role lookup, a missing Unit Admin dashboard branch, and a branch label that never refreshed from the authoritative profile. Startup also seeded an unwanted ADMIN system record alongside TENANT_ADMIN. The current source failed nine existing permission/selection regression checks before the fix.

## Implemented locally

- TENANT_ADMIN is the canonical tenant role in creation, signup, selection, labels, and existing role references. Removed fixed database UUIDs from user-management role classification.
- Sidebar permissions use the live backend union, honoring empty permissions. Role names and archetypes no longer manufacture navigation capabilities. Unit-only navigation is labeled Units and excludes Branch, Markets, Company, SSO, and branch settings without their explicit capabilities.
- Dashboard selection preserves exact assigned IDs, prefers profile assignment metadata, rejects ambiguous legacy names, and preserves the configured primary when omitted from management catalogs. Unit Admin has an explicit dashboard, with jobs filtered by assigned unit and branch. Tenant dashboard rendering also requires a tenant capability.
- Fresh profile office name, unit, timezone, and working hours replace stale branch storage. Missing office values clear old account values rather than persisting Assigned Office. The clock no longer fabricates office working hours when absent.
- The backend permission guard no longer bypasses checks using admin role names. Affected tenant/SSO/domain writes require explicit capabilities. Market mutations require tenant settings. Branch directory reads and unit/job data are scoped. Unit Admin cannot read/edit other units, create/delete units, or move their own unit to another branch. Unit management UI hides unavailable directory actions.
- Existing custom-role permission bundles are no longer overwritten by startup seeding. Catalog reads honor empty permission arrays. Startup preserves a valid primary role assignment.
- Added an atomic, repeatable startup migration in ats_backend/src/auth/services/canonical-system-roles.ts. It remaps legacy ADMIN system references to TENANT_ADMIN, preserves custom-role IDs and permission bundles, updates invitation system references, and removes the legacy system record. Colliding legacy default role display names get a unique migrated label. Existing platform system roles receive their explicit platform capability during this one-time legacy migration.

## Verification

- Frontend: all 40 tests passed; final TypeScript check passed, including unit-page action visibility changes. Unit management JSX syntax validation passed.
- Backend: all 50 tests across 15 suites passed, including new permission, branch, unit, and job-scope tests; TypeScript passed.
- PostgreSQL migration integration test passed against session-local temporary tables, with rollback: legacy-only and duplicate-role cases, foreign key preservation, permission preservation, and repeated execution.
- Both repositories passed git diff --check using their configured Windows line-ending handling.
- No application database records were changed by validation. The startup migration has not been executed against application tables. No application services were started or deployed.

## Remaining verification boundary

The configured database returns no account matching sahadeb@enfyjobs.com, including explicit ats schema queries. The production screenshot's exact account mapping remains unverified. Deployment and authenticated production browser verification are still required. Existing unrelated scratch-file deletions were left untouched.

Status: DONE_WITH_CONCERNS — code changes implemented; production deployment/account verification outstanding.
