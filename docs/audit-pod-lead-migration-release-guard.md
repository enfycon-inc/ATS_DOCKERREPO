# Audit & Fixing Plan: Pod Lead migration blocked by release guard

## Executive summary
Deployment rejected migration 20261015030000_pod_lead_assignment_grant before execution. Traffic stayed unchanged according to the supplied release log. SSH and Docker login succeeded; the credential-storage warning is not the reported failure. The permission grant is data-changing despite being additive in business meaning. The earlier implementation tested SQL correctness but omitted release-guard acceptance.

## Root cause
deployment/bluegreen/release.py:83-103 requires rollback review plus an explicitly recognized reviewed exception for any UPDATE/INSERT. Existing Account Manager grants and submission ownership changes have narrowly validated exceptions. The Pod Lead migration has the rollback marker but no corresponding exception, so its UPDATE and audit INSERT statements trigger rejection. Local read-only invocation of the validator reproduced the exact error. Normalized LF SHA256 of the already committed migration: 02293f337df6f06743b5ef7f40fe4b154dbfe485aa6cd5af957c7f0788fac151.

## Impact radius
The release was not activated and this new migration was not executed by the rejected invocation. The existing live permission state remains unverified. Do not bypass the guard or run the permission SQL manually to work around deployment. Do not edit the committed migration, avoiding Prisma checksum drift.

## Implementation plan
1. Add a reviewed exception in the release controller for the exact migration name and normalized-LF SQL digest above, following the existing exact-content review approach. Keep rollback marker, transaction and five-second lock timeout checks mandatory.
2. Add tests accepting the exact migration with LF and CRLF; rejecting broadened role predicates, added wildcard permissions, extra statements, wrong migration name and arbitrary data changes.
3. Run the release-controller test suite and confirm all existing rejected migration cases remain rejected.
4. Push the root deployment-controller repository when authorized. Retry deployment using that updated controller; the previous backend artifact can be reused through supported workflow inputs. No new permission grants beyond the already approved SQL.
5. After deployment verify migration completion and the Pod Lead profile/assignment action. The audit does not claim live access or deployment verification.

## Rollback plan
Revert only the release exception to reject this migration again. Existing SQL rollback remains available for grants already applied, preserving pre-existing permissions via the recorded audit receipts. Do not rewrite migration history.

## Status
Implemented after user approval. The controller accepts only the exact migration identity and normalized-LF digest above; original migration bytes were not edited. All 45 release-controller tests passed inside a disposable Linux container with no network access and read-only source fixtures. New cases cover LF/CRLF acceptance, wrong identity, expanded role predicates, custom-role widening, wildcard capabilities, extra SQL, and missing review/transaction/lock controls. Existing deployment/rollback simulations also passed; their deployment messages are test output, not production operations. Production has not been redeployed. Push the root repository controller correction and start a new deployment using that updated revision.
