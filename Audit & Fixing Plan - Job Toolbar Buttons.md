# Audit & Fixing Plan: Align Refresh and Settings on the Delivery Head Job Toolbar

## Executive Summary

The screenshot marks the **Refresh** and **Settings** icon buttons. For Delivery Head and higher roles, these should sit on the same row as **New Job** and **Filters**, alongside the job scope tabs. Currently, New Job/Filters are beside the tabs, while Refresh/Settings remain in the table toolbar below, leaving an unnecessary second row.

## Root Cause

- `ats_frontend_main/app/(dashboard)/job-posting/components/job-posting-dashboard.tsx:150-153` sets `showBranchTabs` for Tenant Admin, Branch Admin, Unit Admin, and Delivery Head, then passes it as `actionsBesideLeadingContent` at line 542.
- `ats_frontend_main/app/(dashboard)/job-posting/components/data-table.tsx:420-425` defines `primaryActions` with search (while docked), New Job, and Filters only.
- At line 436, the leading row renders `primaryActions` beside the tabs.
- At lines 455-481, Refresh and Settings are rendered separately inside the lower table toolbar. This is why they remain below the tab row.

## Impact Radius

- Affects the job list view for roles that display the scope tabs: Delivery Head, Unit Admin, Branch Admin, and Tenant Admin.
- Other roles keep their existing toolbar placement.
- No API, permission, job-data, or database changes are required.

## Implementation Plan

1. Add Refresh and Settings to the shared action group only when `actionsBesideLeadingContent` is enabled.
2. Suppress the duplicate Refresh/Settings buttons in the lower toolbar for those roles.
3. Because the sticky dock already portals the shared action group when scrolling, keep Refresh and Settings available there as well.
4. Preserve existing behavior for roles that do not display scope tabs, including their toolbar placement and permission-gated New Job action.
5. Verify the layout at the initial page position, after the table toolbar docks on scroll, and for a role without scope tabs.

## Edge Cases

1. Delivery Head lacks job-create permission: Refresh, Filters, and Settings remain available; New Job remains hidden as before.
2. The page is scrolled: moved buttons remain present in the sticky dock and do not appear twice.
3. Non-management roles: the buttons remain in the current table toolbar location.

## Rollback Plan

Revert the toolbar component change. It is a UI-only change with no database or persistent state impact.

## Approval Gate

No application code has been changed. Please approve this plan before implementation.
