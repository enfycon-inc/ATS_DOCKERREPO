# Audit & Fixing Plan

## Executive Summary
The tracker overrides shared navigation, duplicates branding, and puts variable-height status chips inside the pipeline. Round decisions exist, but rejection rendering does not identify the rejected stage reliably.

## Root Cause
- `ats_frontend_main/app/client-root.tsx:60,188,193,200`: tracker navigation starts closed, overrides shared sidebar state, adds another logo, and hides the standard page header.
- `ats_frontend_main/components/layout/app-sidebar.tsx:121`: tracker-specific offcanvas behavior differs from other pages.
- `ats_frontend_main/app/(dashboard)/utility/submissions/page.tsx:41`: pipeline includes status chips and uses currentRound even after terminal rejection; table headers are left aligned independently of stage centers.
- `ats_frontend_main/lib/submission-tracker.ts:25`: final rejection label hides which interview failed.
- `ats_backend/src/recruiter-submissions/validate-tracker-update.ts:28`: supported round values are PENDING, SCHEDULED, CLEARED, REJECTED and null. Result dialog exposes Cleared and Rejected; UI normally offers Record result only after scheduling.

## Implementation Plan
1. Restore shared sidebar preference and page header; remove tracker-only duplicated logo and offcanvas override.
2. Use explicit column widths in both views; center Pipeline, Current status, Next round and Action headers and content. Keep job and candidate text left aligned for scanning.
3. Remove status chips from beneath pipeline nodes. Add Current status before Next round (five grouped columns, eight flat columns); update all spans and loading states.
4. Limit pipeline width, center it, retain green #008000 checks, solid blue active node with reduced-motion-aware halo, and neutral future nodes.
5. Identify rejected stage from stored round statuses: red X at that node, completed predecessors green, later nodes neutral and inactive. No connecting progress beyond rejection. Show L1 rejected in Current status and no next round.
6. Keep current supported result choices, displaying Selected for CLEARED and Rejected for REJECTED. Require a previously saved SCHEDULED interview with a valid date before recording results, enforced in both UI and backend. A single Update entry point exposes only permitted actions and selects the matching stage remarks. Final-status rejection or early offer/join remains a separate action.
7. Preserve append-only update history, tenant/branch visibility, permission checks, optimistic concurrency and idempotency.
8. Verify types/lint, round rejection/early joining behavior, grouped/flat views, sidebar state, dark mode and narrow screens. Do not mutate production records for UI testing.

## Impact Radius and Edge Cases
Shared shell changes must preserve other pages and saved sidebar preferences. Handle internal-review rejection, L1/L2/L3 rejection, joining with skipped rounds, missing historical values, long names and jobs split across pages. Terminal records remain read-only unless an explicit reopening workflow is separately designed.

## Rollback Plan
Revert this isolated UI change. No migration is needed for this scope; existing IDs, workflow values and historical events remain unchanged.

# System Design Proposal

## Current Architecture Context
The backend owns round state and capability validation; the frontend projects it into a table and append-only history. Remarks templates supply notes, not decision semantics.

## Proposed Solution
Use one shared pipeline projection for nodes and current-status label, derived from canonical workflow codes rather than remark text. Keep round selection separate from application outcome (Offer issued, Joined, Rejected). The immediate UI cleanup uses existing statuses; adding Awaiting feedback, On hold or No show requires a separately approved additive contract/backend change, rather than pretending remarks implement those states.

## Security & Performance Audit
- No new database queries or per-row API calls.
- No tenant, role or relationship IDs hardcoded.
- Backend capability and ownership validation unchanged.
- Historical remarks remain immutable event snapshots.
- Shared contracts remain canonical; no database migration in this proposal.
