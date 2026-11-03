# System Design Proposal — Submission Default Column Order

## Current Architecture Context

The submissions tracker composes its header and row cells from a shared `useTrackerColumns` hook. The hook defines a source-level default, restores optional user-specific order from localStorage, and filters columns according to access scope and view mode. Header drag-and-drop stores each user's chosen sequence under a tenant-and-user-specific key. Actions is fixed at the right edge.

## Proposed Solution

Make a frontend-only change to the default sequence:

```text
Job Reference → Account Manager → Recruiter → Candidate
→ Pipeline → Current Status → Pay Details → Client Terms
→ Job Created → Submitted → Actions
```

The default begins with workflow visibility, then places compensation and client-commercial details after status. Keep existing saved arrangements untouched. No API, database, schema, or migration change is needed.

### Access and layout rules

- Client Terms continues to be permission-gated.
- Account Manager continues to follow existing portfolio visibility.
- Group-by-job continues to omit Job Reference.
- Users can still drag columns to customize their layout; Actions remains sticky and last.

## Security & Performance Audit

- **Authorization:** No permission changes; existing frontend visibility checks remain as-is, and backend authorization is unaffected.
- **Data exposure:** No new fields are requested or exposed. Client Terms stays under its current permission gate.
- **API/database:** No API calls, backend queries, indexes, or schema changes.
- **Performance:** Only changes a static array order; no runtime or network cost.
- **Preference integrity:** No forced migration and no reset of local user choices.

## Design Preview

The attached preview reflects the exact requested column sequence, with Pipeline and Current Status before Pay Details and Client Terms. It is illustrative; production data, permission filtering, and horizontal scroll remain governed by the existing page.

## Implementation Scope

One sequence change in `ats_frontend_main/components/submissions/tracker-columns.tsx`. No other page or role behavior is intentionally altered.

## Rollback

Restore the original `DEFAULT_COLUMNS` ordering. No data rollback is required.

