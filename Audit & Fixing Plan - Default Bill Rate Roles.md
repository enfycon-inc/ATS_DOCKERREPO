# Audit & Fixing Plan

## Executive Summary
Delivery Head, Tenant Admin, Branch Admin, and Unit Admin should have `job:bill_rate:view` by default, alongside Account Manager. Source initialization already includes all four. The prepared deployment migration only repairs Account Manager. The screenshot confirms Delivery Head's deployed archetype still lacks this capability.

## Root Cause
- `ats_backend/src/auth/services/auth-init.service.ts:182-187` includes the capability in all requested default role definitions; line 205 includes them in startup backfill.
- `ats_backend/prisma/migrations/20261031150000_account_manager_client_bill_rate/migration.sql:5,12` targets only Account Manager, leaving the requested four outside that deployment repair.
- `ats_backend/src/jobs/job-commercials.ts:63-81` hides numeric client bill rates without this capability.
Live database verification remains unavailable because the configured connection fails certificate validation. The screenshot establishes missing Delivery Head archetype access; the other three live archetypes are not independently verified.

## Impact Radius
Grant numeric client bill-rate visibility for the four requested system archetypes and their default tenant copies. Existing tenant/branch/unit job access continues controlling which jobs users can access. No new placement-commission permission or job editing permission is introduced. Custom role selections remain administrator-controlled.

## Implementation Plan
1. Add a new idempotent deployment migration targeting `DELIVERY_HEAD`, `TENANT_ADMIN`, `BRANCH_ADMIN`, and `UNIT_ADMIN` in `ats.system_roles`.
2. Append only `job:bill_rate:view` where missing; retain every existing permission.
3. Apply the same additive update to linked `ats.custom_roles` records with `is_system = true` for these archetypes.
4. Keep the Account Manager migration unchanged, avoiding edits to a potentially applied migration.
5. Review SQL for exact role scope and duplicate prevention. Following deployment, verify archetype availability, tenant role capability, and a refreshed session's monthly/hourly rate display.

## Edge Cases
- Already granted permission: no duplicate added.
- Missing/null permission array: initialize only the requested capability.
- Custom role based on an archetype: archetype unlocks the option, but custom selections are preserved.
- Default copies across tenants: update through their system-role relationship without changing tenant or branch scope.

## Rollback Plan
Record affected role IDs and prior permissions before deployment. Restore only those prior arrays if rollback is needed; do not blindly remove access that existed before migration. Refresh affected sessions after permission changes.
