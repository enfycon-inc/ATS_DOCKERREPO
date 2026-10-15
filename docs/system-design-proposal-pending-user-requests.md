# System Design Proposal

Status: approved and implemented.

## Implementation verification

- Pending user requests replaces dashboard account activation/deactivation controls. Only current-unit users with an unapproved, outstanding role request are listed; a zero count hides the panel.
- The schedule and requests share an independently flowing column with 12px spacing. The upcoming list is bounded to the next 10 appointments across L1/L2/L3.
- Review links initialize the existing pending-user review modal. Backend list and approval paths enforce unit scope, role grant limits, and pending-state checks. Rejection clears the outstanding request so it leaves the queue.
- Sidebar links for US IT Candidate Search and Domestic Candidate Search were removed. The sidebar group and applicants page title now read Candidates.
- Nine frontend presentation tests and 23 backend regression tests passed. Both production builds passed. Authenticated browser verification remains unavailable in this environment.

## Additional requested navigation cleanup

The user additionally requested removing the US IT Candidate Search and Domestic Candidate Search sidebar links and renaming Candidates & Talent Pool to Candidates.

Source: `ats_frontend_main/constants/navigation.ts:102` defines the group label; lines 107–108 define the two links. `ats_frontend_main/lib/route-breadcrumb-map.ts:238` supplies the current page title.

Implementation: rename the group and applicants page title to Candidates and remove the two entries from the navigation definition. Retain All Candidates, Upload Single CV, Batch CV Parsing Engine, and Pipeline View. This is navigation/copy cleanup; it does not require deleting search routes, candidate data, or backend permissions. Verify the sidebar and page heading use Candidates and neither removed link remains in the navigation.

## Current Architecture Context

The Delivery Head dashboard currently fetches a paginated unit member list and displays activation/deactivation controls. Its lower section uses one two-column grid ordered Priority jobs, Upcoming interviews, Pod workload, Unit user management. CSS grid rows inherit the tallest panel's height, so a short interviews panel can have substantial space below it before user management begins.

Pending registration requests already exist as users with `isApproved: false`, with requested role and branch/unit assignment fields. Approval/rejection, seat checks, and welcome notifications belong to the existing auth approval workflow. The users page has a Pending tab and review modal, but currently has no request-specific deep-link initialization.

## Proposed Solution

### Dashboard and layout

Latest user clarification supersedes the side-by-side preview: preserve the current visual design. Stack Upcoming interviews and Pending user requests in the same column with a small, consistent 12px vertical gap. Show up to 10 upcoming scheduled interview entries, ordered by earliest upcoming appointment. As the interview list grows to 10, the requests panel moves down naturally. No fixed-height spacer, absolute positioning, or shared grid row may create additional blank space between these two panels. The generated preview's side-by-side arrangement is no longer the approved layout direction.

- Replace Unit user management with **Pending user requests**. Remove activation/deactivation controls and their confirmation dialog from this dashboard.
- Desktop: retain the existing two-column visual design, with Priority jobs and Pod workload stacked in one column, and Upcoming interviews followed immediately by Pending user requests in the other. Each column flows independently.
- On narrow screens keep interviews and requests consecutive with a 12px gap. Keep tables horizontally scrollable within their own panels.
- Hide the request panel when the authorized pending count is zero, without leaving a spacer.
- Show name, email, requested role, and Review request. Use a bounded paginated list rather than a growing staff table. Keep stage labels L1, L2, L3, and Final unchanged.

### Backend and shared contract

Extend the current-unit dashboard response with explicit pending-request list, count, and page fields. Query users with authenticated tenant, branch, and unit predicates plus `isApproved: false`; never infer pending status from inactivity. Gate this section with `user:manage` and the existing current-unit dashboard permission.

Increase the bounded upcoming-interview list from 8 to 10 entries, preserving earliest-upcoming-first sorting across L1, L2, and L3. Fetch at most 10 per round and merge/sort to the next 10 overall; update the displayed limit accordingly. This is an upcoming schedule, not the ten most recently created appointments.

Stop querying the general member directory for this dashboard. Select only fields displayed in the request rows. No new tables, schema columns, hardcoded identifiers, or browser-side filtering of a wider user directory.

### Review interaction

Reuse the existing user approval workflow through a request-specific deep link that initializes the existing review modal. Validate that the selected record remains pending and belongs to the current unit before displaying it and again when approving/rejecting. Audit the linked list and mutation scope so missing or foreign assignments cannot widen access. Preserve existing seat limits, role grant constraints, welcome notifications, and rejection behavior. Do not introduce one-click approval without role validation.

The dashboard refreshes pending counts on return/focus, and removes a request once it is processed. Keep caching keyed to user, role, tenant, branch, unit, permissions, and page.

## Security & Performance Audit

- [ ] Backend filters tenant, branch, unit, and unapproved state for both pending count and rows.
- [ ] No pending requests or actions returned without the necessary granular permissions.
- [ ] Missing assignments fail closed; foreign or already-processed request IDs are rejected by the review path.
- [ ] Preserve role grant limits and account approval checks; do not elevate access based on requested-role text.
- [ ] One existing dashboard API call; bounded rows and pagination; no per-row requests.
- [ ] Shared response types are synchronized; no database schema changes.

## Verification and Rollback

Test pending-only filtering, current-unit isolation, permission denial, zero-request visibility, pagination, already-processed requests, and valid review initialization. Verify alignment at desktop and mobile widths and confirm L1/L2/L3/Final labels remain unchanged. Run relevant approval regressions and both build/type checks. Browser visual verification depends on an accessible app or preview session; report any remaining access limitation explicitly.

Rollback only the pending-request response additions, dashboard panel/layout changes, and request deep-link initialization, preserving unrelated work and existing unit isolation safeguards.

## Visual Preview

The accompanying generated mockup shows the interviews/request row with illustrative data. It is a layout preview, not a screenshot of an implemented change.
