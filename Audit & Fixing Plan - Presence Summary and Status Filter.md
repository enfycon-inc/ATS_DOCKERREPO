# Audit & Fixing Plan: Presence Summary and Status Filter

## Executive Summary

The active users table already displays a per-user presence badge for profiles with `user:presence:view`, but it has no presence filter. The shared navbar has no team-presence summary. The requested counts cannot safely be derived from the currently loaded table page: that page is paginated, and the active/away/offline values come from Redis heartbeats.

The solution needs an authorized, scope-limited aggregate endpoint, a presence filter in the users directory, and a navbar popover whose count cards open a user list filtered to the chosen status. The design preview is displayed in the conversation.

## Root Cause

- `ats_frontend_main/components/users/users-directory.tsx` constructs URL filters for search, city, and role, and renders presence per row when `user:presence:view` is present. No presence state is included in filter state or passed to the backend.
- `ats_backend/src/user-management/user-management.service.ts` validates only search, city, role, and sort values. It pages the SQL user list before decorating those rows with presence, so a status filter added only in the frontend would search just the current page.
- `ats_backend/src/user-management/session-tracking.service.ts` classifies presence using expiring Redis heartbeat observations (active under five minutes, away when recently seen but not active, otherwise offline). It can batch-fetch presence by user IDs but has no scoped aggregate operation.
- `ats_frontend_main/components/layout/navbar-right.tsx` is the shared right-side navbar. It has no team presence component or summary API call.
- `ats_backend/src/user-management/management-policy.ts:managementScope` already supplies tenant and branch/unit scoping. The existing `/api/user-management/users` activity view requires presence or activity permissions and returns paginated user rows.

## Impact Radius

- Active users directory: adds one filter and query parameter; pagination, sorting, search, and other filters must combine with it.
- Navbar: visible to the active role only when it has `user:presence:view`; current defaults include this permission across built-in roles.
- Backend: one summary endpoint and one paginated status-filter path; both must use the actor's current tenant and management scope.
- No schema changes are expected. “Logged in today” uses the persisted successful-login timestamp and the tenant's configured timezone; if telemetry cannot record a login, that limitation must be reflected in the UI.

## Implementation Plan

1. Add `presence` to the user directory API contract and validate accepted values (`active`, `away`, `offline`, `unknown`) server-side. Apply the filter before final pagination so it works across all matching scoped users, not only the loaded page.
2. Add a read-only `GET /api/user-management/presence/summary` endpoint guarded by `user:presence:view`. Return scoped counts for logged in today, online, away, and offline, plus a small recent-activity preview if available.
3. Compute counts only for active approved users in `managementScope(actor)`. Use one bounded database query for the scoped candidate IDs and a batched Redis presence read; cache the aggregate briefly to avoid repeating wide scans for every navbar refresh. Cap or chunk work and degrade to an explicit unavailable state when telemetry is disabled or the presence store fails.
4. Add a compact active-user status dropdown in `navbar-right.tsx`. Poll at a restrained interval, revalidate on focus, and refresh when active role/scope changes. Do not fetch or render for roles without `user:presence:view`.
5. Make each count card open a scoped list sheet with user name, role, branch/unit, presence badge, last active, and last login today where available. “Logged in today” opens the same list filtered to today's login cohort. Fetch list pages on demand rather than embedding all names in the summary response.
6. Add an “All statuses / Online / Away / Offline / Unknown” filter to the Active Users controls and synchronize it with the URL and backend. Preserve all existing filters and server pagination.
7. Add regression coverage for permission denial, cross-tenant/branch/unit scoping, count consistency, combined filters before pagination, telemetry unavailable, and empty status results.

## Edge Cases

1. Telemetry is disabled or Redis is unavailable: show “Live presence unavailable”; do not label all users offline or show misleading zeros.
2. A branch/unit has no matching users: counts are zero and the clicked list shows an empty state.
3. A user logs in through a provider session without complete tracking claims: logged-in-today uses the existing stored login timestamp and may be unavailable for that login; surface the summary timestamp and avoid implying perfect real-time authentication coverage.
4. Active role or branch/unit changes while the popover is open: discard stale data and refetch using the new scope.
5. Large tenants: use bounded/chunked Redis reads and a short-lived scoped aggregate cache; never return an unbounded roster in the navbar response.

## Rollback Plan

Remove the navbar component, summary endpoint, and presence query/filter wiring. Keep existing per-row presence behavior unchanged. No schema rollback is required.

## Approval Gate

Await user approval before implementation.

## Follow-up Audit: Navbar Does Not Match Approved Preview

- **Observed:** the desktop screenshot shows only a “Team + online count” trigger. Logged-in-today, away, and offline counts require an extra click.
- **Root cause:** `ats_frontend_main/components/layout/team-presence-navbar.tsx` rendered a single summary button and placed all count cards inside a click-open panel. The approved desktop design called for four compact, visible, clickable status counts in the navbar.
- **Impact:** the navbar presence summary is less discoverable; the backend, scope enforcement, socket updates, and roster sheet are unaffected.
- **Correction:** show Today, Online, Away, and Offline counters inline at wide desktop widths, each opening its matching roster; keep the compact Team/Online trigger and the same details panel for narrower screens.
- **Rollback:** restore the prior single Team/Online trigger in `team-presence-navbar.tsx`. No backend or database rollback is needed.
- **Authorization:** this is a visual correction to the previously approved navbar design and implementation.
