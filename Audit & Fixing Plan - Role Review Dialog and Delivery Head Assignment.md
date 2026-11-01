# Audit & Fixing Plan — Role Review Dialog and Delivery Head Assignment

## Executive Summary

Two issues are visible in the supplied screenshots:

1. Opening a pending role request first displays a plain loading dialog with a browser-sized heading. Once requests finish, it is replaced by the styled review modal. The transition causes a visible layout jump.
2. Delivery Heads can review branch requests, but the requested employee role is often removed from their choices. The UI requires all role permissions to already be held by the Delivery Head, and the backend enforces the same permission-subset rule. Admin roles must continue to be denied.

## Root Cause

- `ats_frontend_main/components/users/pending-user-review.tsx:20-27` loads branches, units, roles and request details through separate SWR resources. Before they complete, lines 77-81 render a separate, lightly styled dialog. Its heading and dimensions differ from `RoleRequestReviewModal`.
- `ats_frontend_main/components/users/pending-user-review.tsx:41-49` filters Delivery Head choices to employee-category roles and then applies the generic `role.permissions ⊆ reviewer.permissions` rule. That excludes branch employee roles whose job permissions differ from the Delivery Head's.
- `ats_backend/src/auth/utils/role-request-policy.ts:64-105` calls the existing administrative-role guard, then requires every requested role permission to be held by the reviewer. This mirrors the UI restriction.
- `ats_backend/src/auth/services/auth-user.service.ts:885-895` independently rechecks the same policy during approval. A UI-only adjustment would therefore still fail at the API.
- `ats_backend/src/auth/utils/admin-role-assignment-policy.ts:31-43,56-65` detects administrative roles by system/name and elevated permissions, and explicitly denies Delivery Heads. This safeguard is correct and will remain enforced.
- `ats_frontend_main/components/users/pending-user-review.tsx:36-53` treats Delivery Heads as unit-scoped because it only recognizes `branch_admin:manage` as branch-wide. Its unit options are then restricted to the Delivery Head's current unit, rather than other units in their branch.
- `ats_backend/src/auth/auth.controller.ts:698-719` allows callers other than Branch Admins to choose `branchId`, so role-option retrieval should also force Delivery Heads to their own branch.

## Impact Radius

- Pending-user review modal loading, error/retry, role selection and approval.
- Delivery Head approvals and role-request notifications (`role-requests.service.ts` uses `canGrantRequestedRole` to identify eligible reviewers).
- Branch and unit selection in the review modal.
- Role-list visibility for Delivery Heads. Recruiter, Account Manager, Unit Admin, Branch Admin and Tenant Admin authorization behavior must not be broadened.

## Implementation Plan

1. Replace the plain loading/error fallback with the same dialog shell/header as the final review modal. Keep a compact skeleton, loading status, retry/error state and Cancel action inside it to avoid the heading and layout jump.
2. Classify Delivery Head as branch-wide for this workflow. Keep their branch fixed to their own branch and offer units only from that branch; keep unit-only reviewers restricted to their own unit.
3. For Delivery Heads, show all eligible employee roles in their branch regardless of whether the Delivery Head personally holds every permission in those employee roles. Continue to exclude roles that are administrative by system role, name or elevated admin permission.
4. Apply the same narrow Delivery Head employee-role rule in `canGrantRequestedRole`; preserve tenant matching, request branch/unit matching, and `assertRoleAssignmentAllowed`. Keep API-side checks authoritative.
5. Force the role-list endpoint to use the Delivery Head's branch, even if a client supplies a different branch query parameter.
6. Add/adjust focused tests for ordinary employee-role grants, cross-branch/unit denial, stale request versions, and denial of Tenant Admin, Branch Admin, Unit Admin, and custom roles containing elevated admin permissions.

## Edge Cases

- The requested user or role request changes while the dialog is open: keep request-version conflict handling and provide a recoverable error state.
- Delivery Head has no branch, or a requested office is outside their branch: do not expose selectable roles or allow approval.
- A custom role is labelled as an employee role but contains tenant, branch or unit administration permissions: classify it as administrative and deny it.
- A role is branch-wide or system-wide but the target request has a different unit: allow only when its role scope is compatible with the selected target unit.
- One of the modal's option or request calls fails: retain the same dialog layout and show Retry instead of switching to a differently styled screen.

## Rollback Plan

Revert the focused frontend and backend changes. Existing role assignment remains protected by the current permission-subset check and administrative-role guard; no schema or migration rollback is required.

## Approval Gate

No application code or configuration has been changed for this request. Proceed only after the user approves this plan.
