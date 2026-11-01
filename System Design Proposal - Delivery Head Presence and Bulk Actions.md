# System Design Proposal: Delivery Head Presence and Bulk Actions

## Current Architecture Context

The active-users page gets the active role from `/api/auth/me`. Online status is conditionally rendered from the effective `user:presence:view` capability; backend presence data additionally depends on session tracking being enabled. Previously only leadership/admin built-in roles received the capability. Production replicas may skip application bootstrap, so an additive Prisma data migration is needed as well. Custom roles are independently configured.

Bulk actions are exposed only when the selected users have a common allowed action. A mixed selection can make that intersection empty, and the current toolbar hides the entire menu while still displaying the selection count.

## Proposed Solution

### Presence

- Add `user:presence:view` to every built-in system role and existing built-in tenant role copy using an additive migration and idempotent bootstrap sync. Newly seeded built-in roles inherit it.
- Preserve administrator-defined custom-role permission choices. Do not grant `user:manage` as a substitute for presence visibility.
- Continue using the existing profile permission gate and telemetry warning. Keep the presence API permission protected.

### Bulk action control

- Replace separate selection text and Actions button with one blue, compact count button, e.g. **25** with a down chevron.
- Keep the count button visible whenever selection is nonempty. On open, show only actions that are permitted for every selected user; if there are no shared actions, show a clear explanation and “Clear selection”.
- Keep the backend's per-action authorization and scope validation unchanged.

The visual design preview is displayed above and uses the existing active-users table style.

## Security & Performance Audit

- **RBAC:** preserve backend permission and member-scope enforcement; no role-name checks or UI-only authorization.
- **Least privilege:** grant only the presence capability to built-in roles; do not broaden account-management access. Existing tenant and branch/unit scope remains enforced by `managementScope`.
- **Data scope:** existing presence responses remain tenant-scoped and permission-gated.
- **Performance:** role synchronization is an additive, bounded role update; bulk action availability is derived from already-loaded selected rows and adds no API call.
- **Data integrity:** no schema change; an idempotent role-permission data migration appends one capability while preserving existing permission entries and user data.

## Approval Gate

The design and preview were approved; implementation is in progress.
