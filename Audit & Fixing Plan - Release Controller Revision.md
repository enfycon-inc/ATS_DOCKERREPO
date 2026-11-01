# Audit & Fixing Plan

## Executive Summary
The release is running an older controller that does not contain the reviewed bill-rate migration exceptions. The corrected controller remains modified locally in the orchestrator repository. Updating the backend migration image alone cannot update the controller supplied by the orchestrator workflow.

## Root Cause
- The supplied server traceback rejects general data changes at `release.py:299`. In the current local file, line 299 defines `bill_rate_grants`; the general rejection is at line 304. This proves the executing file differs from the local corrected file.
- `deployment/bluegreen/release.py:299-304` locally permits only the two exact reviewed migration names and SHA-256 contents. Git status shows this file is still modified locally.
- `.github/workflows/deploy.yml:344` checks out the orchestrator workflow revision; line 365 runs controller preparation.
- `deployment/bluegreen/prepare.py:49` encodes the checked-out controller. `deployment/bluegreen/execute.sh` decodes that supplied file and installs it as the server's release controller before execution.
- Therefore the controller is refreshed by deployment, but it is refreshed from the workflow's checked-out revision. A rerun of the same old workflow revision can reproduce the failure.

## Impact Radius
No evidence indicates a migration execution failure or traffic switch: the log reports preflight rejection and unchanged traffic. Both permission migrations require the corrected orchestrator controller. No broader permission or schema exception is needed.

## Implementation Plan
1. Review and publish the existing local controller change in the orchestrator repository, retaining exact identity/content checks for both approved migrations.
2. Confirm the backend image contains the matching reviewed migration contents, including rollback markers, transactions, and lock limits.
3. Start a new deployment from the updated orchestrator revision rather than rerunning the old revision.
4. Verify the deployed controller accepts both migrations and rejects altered grants; confirm migration completion before checking the refreshed user session.
5. Add focused regression coverage for accepted original grants, altered permissions/recipients, and incorrect migration identity. Full Linux release checks should run in CI; Windows cannot import the Linux fcntl dependency directly.

## Edge Cases
- Updated backend with old orchestrator: remains blocked safely.
- Altered SQL with the same migration name: rejected by the exact hash check.
- Rerun pinned to an old workflow revision: still supplies the old controller.
- Already applied permission migrations: retain their checksums and do not edit their SQL again.

## Rollback Plan
If release validation fails, retain current live traffic and investigate without relaxing the general migration guard. Revert the controller commit only if necessary; it must not trigger removal of already granted permissions or edits to applied migrations.
