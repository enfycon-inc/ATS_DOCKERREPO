# System Design Proposal

## Unit Admin and Delivery Head dashboards

Status: approved by the user; Delivery Head implementation completed. Unit Admin redesign is deferred.

## Implementation verification

- Backend and frontend production builds passed.
- 70 focused tests passed across nine suites, covering dashboard ownership, stage counts, current-unit job and submission boundaries, review regressions, member access authorization, idempotency, concurrency, and audit recording.
- The generated frontend dashboard contract matches the backend source contract.
- Live authenticated visual verification remains outstanding: no local application server or signed-in browser session was available during implementation.

## Delivery Head first — revised scope

Approved additions: internal review through the existing audited candidate review workspace, and current-unit user management. The dashboard provides paginated member visibility and activation/deactivation with confirmation, permission checks, self-change protection, concurrent-edit detection, and audit logging. Role grants, invitations, and moving users between units continue to belong to their existing management workflows.

Implement the Delivery Head dashboard first; defer Unit Admin changes. Keep the proposed Delivery Head layout and add a prominent interview pipeline directly below the summary cards:

**Total submissions → L1 → L2 → L3 → Final**

- Total submissions: all authorized submission records for jobs in the current unit and the selected submission date range. Count submissions, not unique candidates.
- L1, L2, L3: mutually exclusive current-stage counts for in-progress submissions, using the existing `currentTrackerRound` progression and `CLEARED` status. Pending internal approval remains in a separate Awaiting approval count. An approved submission awaiting its first interview belongs to L1; clearing L1 moves it to L2, and clearing L2 moves it to L3.
- Final: submissions with all rounds cleared awaiting a decision, plus selected, offered, or joined submissions. Display a breakdown of Awaiting decision, Selected, Offer issued, and Joined. Explicit final outcomes take precedence over round state because the existing workflow permits documented round bypasses.
- Rejected, not selected, and withdrawn outcomes appear separately as Closed unsuccessful; they must not remain in active interview stages. Cancelled interviews remain at their current unresolved round, with cancellation visible in the stage breakdown.
- Each interview stage shows pending/scheduled/awaiting-feedback counts where applicable. Default later-round `PENDING` values must not count a submission in every round.
- Clicking a stage opens the submissions tracker with matching stage and current-unit filters. Reuse the exact aggregate predicate for the drill-down list so the count matches the results.
- Label this as Current interview pipeline; cumulative round participation, if added later, must be separately labeled. Total submissions includes approval and closed records, so the four stage counts alone need not equal the total.
- Keep priority jobs, pod workload, and upcoming interviews beneath this pipeline. All sections remain permission-gated and current-unit scoped.

Extend validation with stage transitions, documented bypasses, default pending rounds, internal approval, cancelled appointments, unsuccessful outcomes, and count/drill-down consistency.

## Current Architecture Context

- Next.js renders role-specific widgets from `ats_frontend_main/app/(dashboard)/dashboard/page.tsx`, using the shared dashboard context and backend profile.
- The Unit Admin view currently has three job counters and a basic jobs table. Its `getUnitDashboardJobs` helper filters by branch and business unit in the browser.
- The Delivery Head component currently implements a recruiter sourcing workspace and fetches submissions separately. It needs a delivery management view.
- The Unit Admin routing condition checks `unit_admin:manage` before the Delivery Head condition. Delivery Head templates also grant this permission, so delivery heads can receive the Unit Admin view.
- NestJS already has unit ownership checks and staff scope tests. Jobs listing scope currently contains broader permission exceptions; browser filtering alone is insufficient to guarantee current-unit isolation.

## Proposed Solution

### Ownership and access

Both dashboard experiences manage only the authenticated user's current business unit within their current branch and tenant. Resolve these identifiers from verified server-side user membership; never trust identifiers supplied by the browser. Reject missing, inactive, or inconsistent assignments without falling back to a branch or tenant listing.

Use the selected dashboard role only to choose presentation. Authorize every read and action through granular permissions and server-side resource ownership checks. A role switch must never widen data access. The dedicated unit dashboard endpoint always remains current-unit scoped, including for users with additional permissions.

### Unit Admin experience

- Header: unit name, branch, and “Current unit only” scope badge.
- Summary: active jobs, pending job approvals, active unit members, and active pods; each metric requires its underlying read permission.
- Attention queue: pending requisitions and jobs without pod/recruiter assignments.
- Unit team and pod workload: bounded lists of assigned staff, pods, and open requisitions.
- Quick actions: manage unit members, manage pods, review jobs, and unit settings, only where existing granular permissions allow them.

### Delivery Head experience

- Same fixed unit header and scope badge.
- Summary: active jobs, submissions, scheduled interviews, and joined candidates, based on existing canonical workflow values.
- Delivery pipeline: aggregate submission stages for jobs owned by the current unit.
- Priority jobs: priority, client, assigned pod/recruiter, submission count, and status.
- Pod workload and action queue: unassigned jobs, screening awaiting action, and upcoming interviews where permissions allow access.
- Actions open the existing management screens; their backend reads and writes must independently enforce the same unit boundary.

### Backend and API contract

Add `GET /api/business-units/current/dashboard` before dynamic `:id` routes. Return one typed response containing unit identity, permission-eligible metrics, bounded attention/job/pod/team lists, and pagination metadata. Use a shared TypeScript contract consumed by frontend and backend. Omit inaccessible sections instead of returning unauthorized totals or misleading zero counts.

Filter every query by tenant, branch, and current unit. Submissions must join through jobs owned by that unit; recruiter membership alone does not establish submission ownership. Validate linked pods, recruiters, users, and jobs on every action. Audit the related jobs, submissions, pods, and unit staff endpoints used by dashboard links and close scope gaps required for this workflow.

Define scheduled interviews from scheduled interview rounds; do not count passed rounds as scheduled. Separate offers and joins, and use existing status definitions. Label all-time versus date-filtered metrics explicitly. Do not add financial metrics unless existing placement ownership and permission checks support them.

### Frontend integration

Replace the minimal unit view and recruiter-style delivery view with shared unit dashboard components and distinct permission-aware sections. Correct routing precedence so selecting Delivery Head renders the delivery view. Remove duplicate full-list loading for these two views. Use a cached data hook keyed by user, tenant, branch, unit, and selected view, with loading, retry, empty, and assignment-required states. Clear stale unit data immediately when membership changes.

Use white/slate surfaces, indigo actions, semantic status badges, 18–20px page titles, 14px section titles, and 12px body text. Four summary cards on desktop collapse to two and then one; tables scroll horizontally on small screens.

### Database

No new business tables or duplicated counters. Inspect current indexes and query plans before adding any composite tenant/branch/unit indexes. Select only displayed fields, group aggregate queries, paginate detail lists, and avoid per-row requests. Cache only with complete authorization and scope keys and short freshness windows.

## Security & Performance Audit

- [ ] Tenant, branch, and unit predicates applied on the backend to every aggregate and list.
- [ ] Missing assignments fail closed; no hardcoded or fallback scope identifiers.
- [ ] Direct API requests and mutations reject foreign tenant, branch, unit, staff, pod, and job IDs.
- [ ] Permissions control each section and action; role names only select presentation.
- [ ] One dashboard request; bounded queries and list sizes; no N+1 requests.
- [ ] Shared response types; sanitized errors; no raw query or database errors in the UI.
- [ ] No broader-permission or crafted-query bypass of the current-unit dashboard boundary.
- [ ] No submission, candidate contact, or placement details returned without their permissions.

These are implementation acceptance criteria, not claims of completed verification.

## Validation Plan

Backend tests cover both dashboard permission bundles, missing assignments, unauthorized metrics, foreign IDs, broader permissions, submission ownership through jobs, and mutation ownership. Frontend checks cover selected-role routing, permission visibility, unit changes, empty/error states, responsive layout, and canonical metric definitions. Run relevant existing unit-scope tests and both application type/build checks after implementation.

## Visual Preview

A generated design preview accompanies this proposal. All displayed unit names and numbers are illustrative; the implementation will use authorized live data.
