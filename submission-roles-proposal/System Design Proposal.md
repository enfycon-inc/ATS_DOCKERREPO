# System Design Proposal — Role-aware submission table and stage tabs

## Current architecture context

- The submission tracker is a shared frontend page at `ats_frontend_main/app/(dashboard)/utility/submissions/page.tsx`, driven by the typed tracker contract and URL filters.
- The table column set is currently shared for every viewer. It includes both `manager` and `recruiter`; the current person column represents the job owner/account manager, while the recruiter field represents the submission owner/submitter.
- The backend centralizes tab predicates in `ats_backend/src/recruiter-submissions/tracker-workflow.ts`. Rows and counts use this shared predicate, which is a good consistency point.
- At present `interviews` is defined as `final_status = 'SUBMITTED'`. This includes submissions waiting for the next round to be scheduled, explaining why “L1 pending” can appear under Interviews.
- Round statuses already exist: `PENDING`, `SCHEDULED`, `AWAITING_FEEDBACK`, `CLEARED`, `REJECTED`, and `CANCELLED`. Round key filters exist for L1/L2/L3, so there is no need for schema changes.
- The account-manager portfolio is represented by the explicit `job:submit_owned_jobs` permission (`filterAccess.portfolio`), rather than a role label alone. The client already has per-user and per-permission column capabilities.

## Proposed experience

### 1. Keep the primary tabs, make each label truthful

Retain `All`, `Needs review`, `Interviews`, `Offers`, `Closures`, and `Closed` as the top-level workflow buckets. Define them as disjoint current outcomes and calculate both rows and badges from the same backend predicate:

- **All:** every submission visible to the current user.
- **Needs review:** internal approval is pending (`PENDING_APPROVAL`).
- **Interviews:** an actual interview is scheduled or awaiting feedback in the current active round. Exclude `PENDING`, `CLEARED`, `REJECTED`, and `CANCELLED` round states. Keep historical completed rounds visible in the row’s pipeline, but do not treat a cleared round as an active interview.
- **Offers:** selected / offer-issued outcomes (`SELECTED`, `OFFER`).
- **Closures:** joined (`JOIN`).
- **Closed:** terminal unsuccessful outcomes (`REJECTED`, `NOT_SELECTED`, `WITHDRAWN`) and the existing paused-closed workflow condition.

Counts and row queries must call the same predicates to avoid tab-count mismatches. Closed-job pending submissions remain governed by the current paused-workflow rule.

### 2. Show round/status quick filters beside the tabs in the All view

When **All** is selected, use the currently empty space on the right side of the top tab strip for compact round/status filters: **L1, L2, L3**, followed by status choices **Pending, Scheduled, Awaiting feedback**. This directly exposes the common stage queues without adding more primary workflow tabs. Keep the quick filters on one line at desktop widths; at narrower widths let them wrap or move into the existing Stage filter area rather than causing horizontal overflow. Visually group the round chips and status chips, and show selected chips with the existing blue active state.

On other top tabs, retain the existing Stage selector. In **All**, the quick filters should be the compact shortcut for round plus status; selecting a quick filter updates the same canonical URL state (`round`, `roundStatus`) as the detailed Stage controls. Keep the full statuses (**Cleared, Rejected, Cancelled**) available from the Stage filter/details because they are less common in the highlighted quick-filter area. Keep the selected high-level tab and round/status filters as an explicit intersection, and provide removable active-filter chips/reset behavior.

“Pending” means the round exists in the workflow but is not scheduled. It remains available in **All** + a round/status filter, but not in the **Interviews** tab. “Scheduled” and “Awaiting feedback” are active interview states. The Interviews tab still means only those active interview records, across rounds.

### 3. Make owner/submitter columns match the viewer’s permitted scope

- **Account-manager portfolio view:** hide the Account manager/job-owner column because that identity is implicit in the owned portfolio. Keep **Recruiter** visible because it identifies who submitted the candidate. Do not hide or rename it as “Created by.”
- **Recruiter view:** keep **Recruiter** visible as submission attribution. Keep the Account manager/job-owner column only if the viewer’s permitted submission scope includes jobs owned by other managers; otherwise it is also implicit.
- **Delivery head / branch / unit / tenant views:** retain both columns where the explicit permissions allow viewing multiple owners and submitters.
- Drive visibility from effective permission/scope metadata (for example the existing portfolio access signal), not hard-coded role-name checks. The API remains the authority for the data fields; column hiding is a presentation choice only.

When a column is hidden, remove it from the chooser, sorting choices, persisted column layout, and rendered table together. Keep existing stored layouts migratable so users do not get a broken table after the column policy changes.

### 4. Suggested table and filter layout

For an account manager: **Job | Recruiter | Candidate | Pay details | Client terms (permission-gated) | Pipeline | Current status | Submitted | Actions**.

For a recruiter: **Job | Account manager (when cross-owner scope permits) | Recruiter | Candidate | Pay details | Pipeline | Current status | Submitted | Actions**. Keep client terms subject to the existing explicit permission check.

Keep search, account manager, recruiter, stage, and time period above the table. Place round-status chips immediately below Stage only when a round is selected. Show selected filters as removable chips; a one-click reset should restore the viewer’s default scope without changing authorization.

## Data/API and implementation touchpoints

- **Backend:** update `trackerBucketConditions` so the Interviews predicate checks active interview statuses in the currently relevant round(s), in addition to non-paused job workflow. Avoid a per-row follow-up request; use the existing L1/L2/L3 status columns.
- **Counts:** use these same SQL predicates for row filtering and badge counts. Ensure `dashboard_interviews` definitions use the same business meaning or label their different scope explicitly.
- **Frontend:** consume the existing `filterAccess.portfolio`/effective scope to select the owner column policy; update column availability and saved-layout migration in `components/submissions/tracker-columns.tsx`.
- **Filtering:** preserve round and round-status URL parameters; do not overwrite other filters when switching the round status. Ensure the status options are sourced from the canonical `InterviewRoundStatus` contract.
- **Database:** no schema change or new duplicated status field is required.

## Security and performance audit

- [x] Backend tenant, branch, unit, and submission authorization remains unchanged; UI column visibility does not grant access.
- [x] Continue selecting only permission-authorized fields, especially client rate/terms.
- [x] Avoid role-name checks; use explicit permissions and the existing scoped portfolio signal.
- [x] Use one list/count response and existing indexed status fields; no N+1 fetches or new table scans per row.
- [x] Keep tab counts and rows on the same predicates and SQL query context.
- [x] No schema expansion; frontend/back-end status types remain canonical.
- [ ] During implementation, confirm query plans/index support for round status filters on production-sized submissions and verify tenant scoping in every list/count path.

## Preview limitations

The image-generation tool is not available in this session, so this artifact includes a native SVG design preview rather than claiming a photo-rendered mockup. It uses the existing EnfySync blue/neutral style and illustrative records. The SVG can be opened or viewed inline alongside this proposal.

## Approval checkpoint

Do you approve this system design proposal? Should I proceed with the implementation?
