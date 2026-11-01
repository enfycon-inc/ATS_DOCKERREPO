# System Design Proposal — Role Review Dialog and Delivery Head Assignment

## Current Architecture Context

The pending-user review component fetches the office lists and roles together, and the specific request separately. While those requests load it renders a second modal implementation. The final review dialog has a different design, which accounts for the jump in the screenshot.

Role authorization is checked in both the UI and API. The API's role-request policy requires a reviewer to possess every permission in the requested role. An administrative-role policy separately blocks elevated roles. Delivery Heads have `unit_admin:manage` in their system permissions but are branch-scoped for this workflow; the UI currently interprets them as unit-scoped.

## Proposed Solution

### Review UI

Use one modal shell for loading, error and ready states. In loading state, preserve the loaded modal's compact title and dimensions, and render a skeleton for the request summary, office scope and role options. Display retry errors within that shell. This is presentation-only and requires no database change.

### Delivery Head role assignment

Allow Delivery Heads to grant employee-category roles within their own branch without requiring permission-set containment. Keep all existing tenant, branch, unit, request-version and role-scope checks. Continue to deny Tenant Admin, Branch Admin, Unit Admin and any custom role containing the elevated administrative permissions checked by `admin-role-assignment-policy.ts`.

Treat Delivery Heads as branch-scoped in the modal: their branch is fixed to their own; unit choices are limited to that branch. Unit Admin reviewers remain fixed to their own unit. The role-list endpoint must independently constrain Delivery Heads to their branch so a crafted query cannot enumerate roles from other branches.

### API and data

No new endpoint or database column is required. The existing review and approval endpoints remain in use; the policy change is made consistently in the shared backend decision function and approval validation. Existing version checks continue to prevent approving a replaced request.

## Security & Performance Audit

- **Tenant isolation:** retain tenant-scoped role lookup and user/request checks.
- **Branch isolation:** reviewer must have an in-scope branch; Delivery Head role lookup and approval are forced to that branch.
- **Unit isolation:** keep role-to-target unit scope validation; Unit Admin remains restricted to its own unit.
- **Admin-role protection:** retain `assertRoleAssignmentAllowed` and deny roles identified by admin system role/name or elevated admin permissions.
- **No UI-only authorization:** backend approval independently applies the Delivery Head employee-role exception and admin deny rules.
- **API calls:** retain SWR request deduplication/caching; this change focuses on eliminating visual state replacement rather than introducing extra requests.
- **Schema:** no database changes or migration.

## Approval Gate

The attached UI image is an illustrative loading-state preview. Application code remains unchanged until this proposal is approved.
