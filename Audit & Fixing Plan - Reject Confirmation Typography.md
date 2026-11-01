# Audit & Fixing Plan - Reject Confirmation Typography

## Executive Summary
The reject confirmation prompt is visibly oversized compared with the rest of the role review dialog. This is a typography collision: the confirmation heading inherits a global responsive `h2` size even though its component only sets font weight. The rejection flow and approval behavior are unaffected.

## Root Cause
- `ats_frontend_main/components/users/pending-user-review.tsx:91-94` renders the confirmation alert dialog. Its `h2` has `font-semibold` but no explicit text size.
- `ats_frontend_main/app/globals.css:219-222` assigns all `h2` elements a responsive size using `clamp(1.75rem, 1.11rem + 3.2vw, 3.75rem)`. That global rule makes this short confirmation heading enormous, as shown in the screenshots.
- The surrounding role review modal uses explicit compact text sizes, so the confirmation should define its own typography instead of inheriting the page heading scale.

## Impact Radius
Only the reject confirmation prompt opened from the pending role-request review window. No API, database, permission, or rejection behavior changes are needed.

## Edge Cases
1. Long user names should wrap naturally without widening the dialog or increasing heading scale.
2. Small screens should keep the prompt readable and within the viewport.
3. Dark mode should retain the existing contrast and colors.

## Implementation Plan
1. Set the confirmation heading to the same compact dialog scale as the role-review title (explicit small text size, semibold weight, and normal line height).
2. Set the explanatory sentence to the site's small supporting-text style.
3. Keep confirmation wording, buttons, loading/disabled behavior, and rejection action unchanged.
4. Run a frontend TypeScript check and production build.

## Rollback Plan
Revert only the typography class changes in `pending-user-review.tsx`. No data or persisted state is affected.
