# Audit & Fixing Plan — Submission Default Column Order

## Executive Summary

The submission tracker already supports draggable, per-user column preferences. Its first-visit default places **Pay Details** and **Client Terms** before **Pipeline** and **Current Status**, which conflicts with the requested order. Update the default sequence so workflow columns appear before compensation/commercial detail columns. Preserve saved personal layouts.

## Root Cause

- [tracker-columns.tsx](C:/Users/deb/enfyProjects/ATS_DOCKERREPO/ats_frontend_main/components/submissions/tracker-columns.tsx:9) defines `DEFAULT_COLUMNS` with `payDetails` and `clientTerms` before `pipeline` and `status`.
- The hook uses this order as the fallback when there is no valid saved preference ([tracker-columns.tsx](C:/Users/deb/enfyProjects/ATS_DOCKERREPO/ats_frontend_main/components/submissions/tracker-columns.tsx:57)).
- The submissions page supplies a per-user, per-tenant local storage key at [page.tsx](C:/Users/deb/enfyProjects/ATS_DOCKERREPO/ats_frontend_main/app/(dashboard)/utility/submissions/page.tsx:339). Consequently, the screenshot can show a previously saved order even though the source default differs.

## Impact Radius

- Affects first-visit/default layout for users without a stored column order.
- Does not change backend APIs, database data, permissions, pagination, sorting, filters, or submission behavior.
- Client Terms remains hidden for users who lack the current pay-rate/placement permission check.
- Account Manager remains hidden when the user's portfolio access requires it; grouped-by-job mode continues to hide Job Reference.
- Drag-and-drop customization remains available and Actions remains last/sticky.

## Implementation Plan

1. Change only `DEFAULT_COLUMNS` to:
   `job, manager, recruiter, candidate, pipeline, status, payDetails, clientTerms, jobCreated, submitted, actions`.
2. Leave saved preference restoration and migration logic unchanged. Existing saved orders are user customizations and should not be reset to enforce a new default.
3. Verify the resulting header order for a user with no saved preference and verify that custom saved order, permission-hidden columns, grouped mode, and sticky Actions behavior remain intact.

## Edge Cases

1. **Existing custom preference:** Keep it exactly as saved; new default applies only when no valid saved order exists.
2. **No Client Terms permission:** Hide that column while keeping the rest of the default sequence in order.
3. **Grouped-by-job view:** Continue hiding Job Reference without moving the remaining columns.
4. **Manager restricted by portfolio:** Continue hiding Account Manager.
5. **Malformed/unavailable local storage:** Preserve the current graceful fallback behavior.

## Rollback Plan

Revert the single default-array ordering change in `tracker-columns.tsx`. No migration or data rollback is needed because this proposal does not mutate stored preferences or server data.

## Verification Plan

After approval, inspect the rendered default order and run the relevant frontend static/build checks. Confirm existing local-storage preferences are not rewritten or reset.

