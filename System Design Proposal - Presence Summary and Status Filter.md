# System Design Proposal: Presence Summary and Status Filter

## Current Architecture Context

Session tracking stores per-tab heartbeats in Redis and classifies a user as online, away, offline, or unknown. The user directory fetches a server-paginated list and decorates only the current page with presence. It does not accept a presence filter. The navbar is shared across roles and currently has no team presence summary. `managementScope(actor)` provides tenant/branch/unit scoping; `user:presence:view` is the existing capability for reading presence.

The preview shown in the conversation places a small presence summary in the blue navbar. Its four status counts are clickable and open a roster sheet. The directory filters gain a Presence status dropdown.

## Proposed Solution

### Backend API

- Add a `GET /api/user-management/presence/summary` read endpoint. Require `user:presence:view`; derive scope exclusively from the authenticated actor and `managementScope(actor)`.
- Return counts only: `{ asOf, telemetryEnabled, loggedInToday, online, away, offline }`. Counts represent active approved users in scope. Do not use caller-provided tenant/branch IDs.
- Count logins using `users.last_login_at` and the tenant timezone's start of day. Return `telemetryEnabled` and an `asOf` timestamp so the UI can disclose stale/unavailable data.
- For Redis status counts, select scoped active user IDs using a bounded query and read their existing Redis heartbeats in chunks. Use a short-lived cache keyed by tenant, branch/unit scope and actor permission scope. On store failure, return `telemetryEnabled: false` or an explicit unavailable summary instead of false offline totals.
- Extend the paginated activity/list request with `presence`. Apply the status selection to the scoped candidate set before selecting page rows; never filter after pagination. Add a matching presence type to the generated shared user-management contract.
- Provide paginated list pages to the sheet on demand, including name/email, roles, branch/unit, presence, last activity, and last login where permission allows. The navbar summary itself remains small and does not carry an unbounded roster.

### Frontend

- Add a `TeamPresenceNavbar` component to `NavbarRight`, gated by the active-role `user:presence:view` permission. Poll around every 30 seconds, refresh on focus and role/scope changes, and display a clear unavailable state.
- Show compact indicators for logged in today, online, away, and offline. Clicking a count opens a responsive sheet containing the corresponding paginated list. All cards remain keyboard accessible and expose labels/counts to assistive technology.
- Add an “All statuses” select to the Active Users filter row. Store its value in the URL and combine it with search, city, role, sorting, and page size.
- Preserve the existing classic royal-blue navbar and enterprise table styling. On narrow screens use a compact icon/count trigger and a full-width sheet.

## Security & Performance Audit

- **Authorization:** gate summary and roster APIs by `user:presence:view`; enforce on the backend regardless of UI visibility.
- **Scope:** every query derives tenant/branch/unit scope from the authenticated actor; no client-supplied scope overrides.
- **Data minimization:** summary returns aggregates only. Names and user details load only after a count is selected and remain paginated.
- **Performance:** one aggregate response serves all four counts; cache briefly per authorized scope; Redis reads are chunked; list rows remain paginated.
- **Consistency:** presence filters run before pagination and compose with existing search, city, role, and sorting.
- **Failure behavior:** Redis/telemetry unavailability is distinct from zero users or offline status.
- **Schema:** no new table or column is needed.

## Approval Gate

The audit and design preview are complete. Await approval before implementation.

## Follow-up: Desktop Navbar Alignment

The approved wide-screen navbar design requires four visible clickable indicators: Today, Online, Away, and Offline. The implementation had collapsed these behind a single Team/Online button. Show the four counts inline at wide desktop breakpoints; keep the compact trigger for narrower widths, with the existing popover and roster sheet unchanged. This is presentation-only and does not alter API payloads, RBAC, presence rooms, or database schema.
