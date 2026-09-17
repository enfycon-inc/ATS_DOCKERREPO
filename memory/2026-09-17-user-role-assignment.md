# Role removal and job delegation investigation

## Symptoms and confirmed causes
- Users & Teams retained Branch Admin and Delivery Head after unchecking them for `am@deb.com`.
- The branch picker wrote `branchRoles`, while Save sent stale `roles`. The current single-branch backend no longer consumes `branchRoles`.
- Name/archetype resolution could match multiple same-named roles across branches. Database inspection found four assignments: two Branch Admin roles (one from another branch), Delivery Head, and BDM.
- Existing-user Keycloak synchronization and JWT guard merged token roles back into database permissions/roles. The 60-second user cache also delayed revocation.
- Earlier delegation logs showed a missing `job:delegate` permission. On September 17 the saved branch-admin role already contained both delegation capabilities. The table still used a mount-time local profile and nested delegation under edit access; the target selector explicitly appended the branch code.

## Changes
- Member form submits exact selected `assignedRoleIds`, including an intentional empty selection. Backend validates same-tenant/branch role resolution before one update of both role columns, rejects a primary role outside the selection, and no longer issues a second conflicting roles update.
- Existing-user authentication uses database roles/permissions and checks the user's saved timestamp before cache reuse. Platform SUPER_ADMIN realm identity remains supported.
- Delegation actions use current profile data, refresh on focus/branch changes, and are labeled Delegate Job independently of edit access. Branch codes are omitted from target labels.
- Preserved the in-progress delegation position field by writing its value into notes, matching the current schema/API. Corrected an existing implicit-any error in navbar role rendering so the frontend type check passes.
- Applied the explicitly requested role removals for `am@deb.com` using a guarded transaction. Both columns now point only to BDM. No role definitions or other users were changed.
- Updated the project architecture blueprint. Preserved pre-existing edits in both service repositories.

## Verification
- Backend regression tests failed before the fixes for invalid/stale role replacement and token-driven role restoration, and pass after them.
- Backend unit suite: 11 tests passed across 4 suites (including signed-token guard tests).
- Frontend role-selection tests: 4 passed, including unchecked roles, empty selection, duplicate names across branches, and foreign-branch IDs.
- Backend build and frontend `tsc --noEmit --incremental false`: passed.
- Browser verification reached the login page; the connected browser has no authenticated session. No credentials were guessed and no real job was delegated.
- Backend processes need to load the new compiled code. Full application startup also runs existing schema/seed hooks, so activation must account for the workspace's in-progress database changes.

Status: code and targeted data correction verified; authenticated browser interaction and running-backend activation remain to be confirmed.
