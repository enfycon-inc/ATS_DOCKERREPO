# System Design Proposal

## Delivery Head — interactive visual revision

Status: approved and implemented. Companion artifact: `audit-fixing-plan-delivery-dashboard-visuals.md`.

## Accepted implementation corrections

- Stage labels are exactly L1, L2, L3, and Final, without descriptions in parentheses.
- Total submissions displays submissions done / submissions required across all non-deleted jobs owned by the current unit, including jobs outside the bounded active-jobs list. The backend sums `submissionRequired` with tenant, branch, and unit predicates. Done uses actual submission records already counted by the pipeline, rather than a separate stored counter.
- Total-card percentage is done / required × 100. A zero target displays “No submission target”; an unavailable target is not converted into zero. Values above the target retain their true numeric percentage while the visual bar stops at its maximum width.
- L1/L2/L3/Final percentages and the distribution chart remain shares of actual submissions, not completion against job targets.
- Eight frontend presentation tests and twelve focused backend tests passed after the metric correction. Both backend and frontend production builds passed.
- A temporary static preview could not be reached by the browser (localhost timeout), so authenticated visual and viewport verification remains outstanding.

## Current Architecture Context

The existing current-unit dashboard already provides the required counts and management workflows. Its frontend renders neutral metrics, clickable but mostly neutral stage cards, two top headers, and unconditional zero-count approval UI. Switching uncached stage filters replaces the whole dashboard with skeletons.

## Proposed Solution

### Layout and visual system

- One compact header: Delivery Head, current unit and branch, fixed scope badge, authorized quick actions, refresh.
- Four colored summary cards: blue Active jobs, violet Submissions, amber Scheduled interviews, emerald Joined candidates. Use icons, subtle tinted backgrounds, clear values, and consistent typography.
- A colored pipeline with Total, L1, L2, L3, Final, stage counts, share bars, and clear hover/selected/focus states. Keep scheduled, pending, feedback, cancellation and final outcome breakdowns visible.
- Add a current-stage distribution chart beside or below the pipeline. Use mutually exclusive L1/L2/L3/Final/Closed stages plus internal review only when its count is positive and visible. Total is the denominator, never an additional chart slice. Include an accessible text legend and clickable stage selection.
- An amber review attention banner appears only when pending approvals exist and the user has screening permission. Hide it and the corresponding approval control at zero. Default the results panel to all submissions.
- Lower sections retain priority jobs, upcoming interviews, pod workload, and unit user management, with semantic badges and compact tables. Workload bars compare actual open-job counts, not invented capacity utilization.
- Responsive layouts use two metric columns on smaller screens and four on wide screens; pipeline cards wrap and charts stack. Tables own their horizontal scrolling.

### API and schema

Use the current `DeliveryDashboard` response and existing current-unit endpoint. No database schema changes, new business tables, duplicate counters, time-series claims, or additional API calls are required for this revision. All-time scope remains explicitly labeled. Preserve the canonical stage-count rules and existing review/account mutations.

### Data loading and interactions

Keep the summary display stable during same-scope stage pagination while the detail panel loads. Never display old-stage rows as current results. Reset review selection and page when its aggregate count reaches zero. Reset cached display state across user/role/tenant/branch/unit boundaries. Preserve review workspace navigation and member confirmation dialogs.

## Security & Performance Audit

- [ ] Every section/action retains its granular permission condition.
- [ ] Existing backend tenant, branch, unit, ownership, and mutation checks remain enforced.
- [ ] No hardcoded tenant/unit IDs, fallback scopes, or illustrative preview numbers enter application logic.
- [ ] Charts derive from authorized aggregate values already returned; no raw queries or external data calls in the frontend.
- [ ] Stage interactions reuse existing bounded API requests and scoped caching.
- [ ] No extra per-row requests or duplicated database metrics.
- [ ] Empty/error states distinguish real zero from unavailable data.
- [ ] No invented growth, conversion, or utilization figures.

These are implementation acceptance criteria, not claims of completed changes.

## Preview and Verification

The accompanying generated mockup illustrates the zero-pending-approval state: no approval banner, chip, or review-only table. Positive-count behavior adds a compact amber review banner above the pipeline. All preview values are illustrative. After approval, verify both approval states, final-review transition, chart selections, responsive layout, dark mode, and permission restrictions against the actual implementation.
