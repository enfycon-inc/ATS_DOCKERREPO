# Audit & Fixing Plan: Delivery Head Presence and Bulk Actions

## Executive Summary

The active-users screenshot shows no **Online status** column. The frontend only renders that column when the active-role profile contains `user:presence:view`. This capability was granted only to selected leadership defaults, leaving recruiter, account manager, BDM, pod lead, and other built-in roles without it. Presence access remains constrained to tenant and branch/unit scope; it does not grant account-management actions.

The bulk action menu is hidden whenever none of its actions is authorized for **every** selected user. Selecting the page (25 users) can include a protected or out-of-scope account, which makes the action intersection empty. The UI then leaves only the “25 selected” label and gives no explanation.

## Root Cause

### Online status

- `ats_frontend_main/components/users/use-management-profile.ts:8-14` obtains the active profile and permissions from `/api/auth/me` using active-role headers.
- `ats_frontend_main/components/users/users-directory.tsx:136-138` adds the Online status column only when `has('user:presence:view')` is true; the row rendering uses the same gate at line 180.
- `ats_backend/src/user-management/user-management.service.ts:99-108` populates presence only when tracking is enabled and the actor has `user:presence:view`. It reports `telemetryEnabled` at line 142.
- Default roles are seeded in `ats_backend/src/auth/services/auth-init.service.ts:182-188`. Its presence backfill previously updated only administrator and leadership roles and their `cr.is_system = true` tenant copies.
- `ats_backend/src/auth/services/auth-rbac.service.ts:36-93` creates tenant system roles from system-role permissions. Existing-role updates preserve their permissions, so the additive migration/backfill must update existing copies.

The screenshot's absent column indicates the active profile does not expose the presence permission. If the permission is present, a disabled telemetry configuration is a separate failure mode and is indicated by the page warning.

### Bulk action button

- `ats_frontend_main/components/users/users-directory.tsx:99-102` computes each action with `every(...)` across selected users, then sets `hasBulkActions` false when the intersection is empty.
- At line 151, the selected count is rendered independently but the action dropdown is rendered only when `hasBulkActions` is true. There is no explanation when selection contains a user the actor cannot manage.
- Backend safeguards already enforce `user:manage`, tenant and office scope, and protected-user restrictions through `auth.controller.ts:412-436`, `auth/user-management-policy.ts:36-68`, and `auth/services/auth-user.service.ts:1011-1040`. The UI fix must preserve these checks.

## Impact Radius

- Presence: all built-in system roles and their tenant copies. Custom roles with administrator-defined permission sets remain unchanged.
- Bulk actions: Delivery Heads and administrators selecting a mix of manageable, protected, self, or out-of-scope users.
- No table schema change is needed. Existing role permission rows may need an additive permission backfill/synchronization, with no removal of existing permissions or user data.

## Implementation Plan

1. Confirm the effective active-role permissions returned by `/api/auth/me` for the Delivery Head profile, and confirm `telemetryEnabled` in the active-users response. Use this distinction to verify whether the deployed tenant has a stale built-in role or disabled presence tracking.
2. Add `user:presence:view` to every built-in system-role template and existing built-in tenant role copy through an additive migration and bootstrap sync; ensure newly seeded built-in roles inherit it. Preserve all other permissions and leave custom roles unchanged.
3. Keep the presence column gated by `user:presence:view`; when permission exists but telemetry is disabled, retain the existing unavailable warning. Do not bypass API authorization or expose presence to ordinary users.
4. Replace the hidden bulk menu trigger with one count-only button displaying the selection count and a downward chevron. It remains available whenever users are selected, even if no action applies to the full selection.
5. Populate the dropdown with only actions permitted for every selected user. If the intersection is empty, show a short explanation and a clear-selection action. Preserve backend validation for every mutation.
6. Verify the all-role permission backfill, telemetry-disabled behavior, and mixed selections containing protected or out-of-scope users.

## Edge Cases

1. Presence permission is present but Redis/session tracking is disabled: keep the column and show the existing telemetry-unavailable notice; do not report everyone offline.
2. A selected set contains the current user: do not offer status-change or session-revocation actions that are disallowed for self, while showing any other action valid for the whole set.
3. A selected set contains a tenant/branch administrator or member from another unit: show the count button, omit actions not valid for all selected users, and explain why no shared action is available.
4. A custom role without presence permission: respect its administrator-configured permission set and do not grant unrelated user-management capabilities.

## Rollback Plan

Revert the UI trigger/menu and role-sync changes. If the additive migration has run, remove only `user:presence:view` from built-in role rows if the workspace owner wants presence disabled; leave all other permissions and user records intact. No schema change is introduced.

## Release Gate Follow-up

The first deployment attempt stopped in the release controller's additive-migration validation because the SQL file lacked the exact `-- ATS: rollback-compatible` marker. The validation failed before `prisma migrate deploy`, so this attempt did not apply the migration. The file already had `BEGIN`, `SET LOCAL lock_timeout = '5s'`, and `COMMIT`; the missing marker has now been added.

## Approval Gate

The implementation was approved. The visual preview shown in the conversation uses a blue count-only **25** action trigger with a downward chevron and its menu open.
