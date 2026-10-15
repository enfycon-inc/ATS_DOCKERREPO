# Audit & Fixing Plan

Status: approved; visual revision and zero-pending approval behavior implemented. Subsequent user clarification changed the total percentage to submissions done / required across all current-unit jobs. See the companion system design proposal for verification details.

## Executive Summary

The Delivery Head dashboard has working stage selection, review actions, and unit staff access controls, but its presentation is mostly identical white surfaces. The approval area remains visible at zero because its render conditions do not test the count, and the initial table is always the review table. The attached screenshot is consistent with this presentation. Findings below are verified from source; this audit did not reproduce the page in an authenticated live browser.

## Root Cause

Paths below are relative to `ats_frontend_main`.

| Location | Finding |
| --- | --- |
| `app/(dashboard)/dashboard/components/delivery-head-dashboard-view.tsx:22` | Initial stage is `review` regardless of whether any pending approvals exist. |
| Same file, line 66 | Internal review banner and button check `submission:internal_screening`, but do not check `pipeline.review > 0`. |
| Same file, line 70 | Awaiting approval filter always renders when pipeline data exists, including at zero. |
| Same file, line 72 | The selected-stage table renders for the default review stage, creating an empty approval table and pagination at zero. |
| Same file, lines 54–64 | Summary metrics contain only labels and numbers on the shared white surface. There is no per-metric color or icon hierarchy. |
| Same file, line 69 | Pipeline cards are already clickable, but inactive cards have the same neutral treatment and there is no stage distribution visualization. |
| `app/(dashboard)/dashboard/page.tsx:256` and component lines 59–63 | A generic welcome/action panel is followed by a second unit header, adding vertical space before useful information. |
| Component lines 29–32 | Stage changes use different SWR keys with `keepPreviousData: false`; the entire dashboard enters its loading skeleton for each uncached stage. This weakens continuity during interaction. |

The screenshot shows a limited viewport with content absent on the left. A full-page overflow problem cannot be established from that image alone. Verify the complete layout at narrow widths before deciding whether changes outside the dashboard are necessary.

## Data Flow and Architectural Context

The dashboard uses SWR and `atsApi.businessUnits.deliveryDashboard` to read the dedicated NestJS current-unit endpoint. The backend already returns summary counts, stage breakdowns, paginated submissions and members, bounded jobs and pods, and upcoming interviews. `pipeline.review` is the aggregate count of `PENDING_APPROVAL` submissions, rather than the length of the current results page.

No evidence requires a schema change or a new analytics endpoint. The existing values support the proposed visuals without invented trends, capacity percentages, or additional data requests.

## Impact Radius

- Delivery Head dashboard presentation, loading behavior, and default selection.
- The parent dashboard header changes only when the selected presentation is Delivery Head.
- Internal review continues to use the existing audited review workspace.
- Current-unit ownership rules, granular permissions, account access protections, stage definitions, and other role dashboards remain intact.

## Implementation Plan

1. Extract readable, reusable metric, pipeline, and section components from the current dense render markup.
2. Use one Delivery Head toolbar containing unit identity, fixed scope indicator, existing authorized actions, and refresh; avoid the duplicate generic panel for this view.
3. Add distinct blue, violet, amber, and emerald metric accents with icons, tinted surfaces, and strong numeric hierarchy. Match light and dark themes.
4. Keep stage cards clickable and add distinct L1/L2/L3/Final colors, visible selection, keyboard focus, and stage-share bars. Add a clickable current-stage distribution chart using the already-returned counts. Provide text counts alongside the chart.
5. Initialize to all submissions. Show the internal approval banner, awaiting-approval filter, and review-specific detail table only while the authorized aggregate pending count is positive. Never render a zero-count approval placeholder.
6. If the last pending review is approved/rejected locally or disappears on revalidation, clear the review selection and reset pagination to the all-submissions view. Distinguish a known zero from missing data or a failed request.
7. Keep stable summary visuals visible while a stage page loads, but show a loading state in the results panel so old rows are never presented as the newly selected stage. Do not retain data across user, role, tenant, branch, or unit changes.
8. Add semantic priority/status badges, pod workload bars based on actual job counts, compact interview rows, and a clearer staff management table. Keep existing actions and confirmation behavior.
9. Make layout containers shrinkable; use responsive cards and table-local horizontal scrolling. Verify at 390, 768, 1024, and 1440px widths.
10. Run visibility/transition tests and existing stage/ownership regressions, type and production-build checks, then visually verify the implemented view against the approved preview.

## Edge Cases and Acceptance Criteria

- Zero pending approvals: no approval banner, approval button/chip, empty approval table, or approval pagination.
- Positive pending approvals plus screening permission: show the review action and exact count; without screening permission, omit the approval action. Submission viewing remains independently permission-gated.
- Last review cleared or moved by another manager: review UI disappears and selection recovers without a blank page or refresh loop.
- No submissions: charts display an honest empty state, with no invalid percentages or fabricated activity.
- Null/unauthorized pipeline or request failure: do not interpret unavailable information as zero pending.
- Current unit/role changes: clear former-scope visuals and rows before rendering the new scope.
- Narrow screen or long unit/member names: no page-level overflow; all actions remain accessible.
- Keyboard and reduced-motion settings: chart segments/cards have text equivalents, focus indicators, and no required animation.
- Interview-round pending counts remain visible; the hide-at-zero rule applies to internal approval UI, not unfinished interview-round counts.

## Rollback Plan

Revert only the new visual revision hunks/components and its tests in the Delivery Head view and conditional parent header. Retain previously implemented backend unit isolation and review/account safeguards. If necessary, revert approval visibility independently from the color/chart changes. Preserve unrelated working-tree changes.
