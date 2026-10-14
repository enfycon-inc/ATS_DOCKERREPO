# System Design Proposal — Submission update window

Approved scope: a single ellipsis action opens one window for L1, L2, L3 and the final outcome.

## Current architecture context

The submissions API owns permissions, tenant/branch visibility, optimistic concurrency and append-only history. Round fields are stored on the submission; history events store immutable snapshots and before/after changes. The former table displayed a primary action beside an overflow menu. Older scheduling entry points used a separate dialog and could attempt an early offer.

## Proposed solution and implemented behavior

- Shared `InterviewRoundStatus` enum: Pending, Scheduled, Awaiting feedback, Cleared, Rejected, Cancelled.
- L1 requires internal approval; L2 requires L1 cleared; L3 requires both L1 and L2 cleared. Disabled fields explain the dependency.
- Scheduling requires a date and time. Feedback and clearance require a previously saved appointment that has taken place. Cancellation and rejection require remarks. Cancelled interviews can be rescheduled.
- Final outcome options: In progress, Selected, Not selected, Offer issued, Joined, Withdrawn. Selection requires all three round clearances; offer requires a saved selection; joining requires a saved offer. Not selected and Withdrawn may close an approved submission before interview completion. Rejecting a round automatically records Not selected.
- `PENDING_APPROVAL` and legacy/internal `REJECTED` remain internal workflow values. These are not additional choices in the six-option final outcome menu.
- Earlier recorded results and their details can be corrected with the round's audit permission and a mandatory reason. Resetting later appointments/results requires explicit confirmation. History retains all original values.
- Changing a final outcome backward, reopening a closed submission, or invalidating a selected/offered/joined submission also requires final-outcome authority. An internal-review rejection cannot be reopened through the interview window.
- Save only changed fields in one atomic update with an expected version and idempotency key. Historical baselines are captured for older records without an event log.
- Configured branch/global remark suggestions are loaded once per editor and filtered by stage. Free text remains available. Saved remarks are text snapshots independent of future template edits.
- The history view displays previous and new values, actor, timestamp, correction reason and any downstream reset.
- The existing scheduling modal delegates to the same editor.

## Security and performance audit

- Backend capability checks independently protect every mutation; UI visibility does not grant authority.
- Existing tenant, branch and record visibility checks run before update/history access.
- No new tenant IDs, role-based grants, external frontend calls or per-row fetches.
- The canonical contract is generated into the frontend and includes typed round/outcome values and correction metadata.
- Existing normalized history storage is reused; no extra round tables or duplicated event snapshots are introduced.
- New inputs reject invalid states, malformed remarks, forged reset flags and inconsistent round sequences.
- Database triggers validate changed status values while preserving untouched legacy records, and reject UPDATE/DELETE of audit entries.
- Audited submissions must be closed using final outcomes; deleting them would erase history and is rejected.

## Deployment

### Approved responsibility policy

Recruiter role bundles, including derived custom bundles, retain submission creation and viewing but lose submission maintenance, scheduling, result, final-outcome, review and rate-edit permissions. Account Manager bundles receive scheduling, all round audits, final outcomes and submission remarks. Existing administrative capabilities and the configured internal-review process remain available. A user explicitly switching to a separately assigned management role uses that selected role's permissions; the API does not combine inactive roles.

`20261015020000_submission_role_ownership` reconciles existing role bundles transactionally. Local/bootstrap initialization applies the same policy. Production skips bootstrap and therefore requires the migration. Request authentication already reloads the active role's current database permissions on every request, so no stale JWT permission grant overrides a migration removal. The read-only window explains responsibility and omits Save. The deployment controller allows the exact reviewed migration checksum only, rejecting modified or forged ownership markers.

Apply `ats_backend/prisma/migrations/20261015010000_submission_round_states/migration.sql`, then deploy the backend and frontend together. No production data was changed during implementation. The migration does not rewrite existing statuses or historical events. Older application versions do not understand the added workflow states; rolling back requires accounting for records written with those states and the history protection triggers.

## Verification

Submission workflow/service tests cover transitions, permission boundaries, tenant visibility, concurrency, correction resets and atomic history. Type checks run for both projects. The actual dialog is rendered separately with illustrative data for desktop and narrow-screen interaction checks; real candidate records are not used for those checks.
