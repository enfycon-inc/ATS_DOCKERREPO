# Delegation branch and unit picker

Symptom: unit list empty; user requested branch selection and same-market units.

Root causes: frontend called business-units/delegation-targets but the literal
controller route was missing, so the request matched :id. The modal swallowed
errors. Existing target service did not filter by segment or include segment
metadata. Submission still only used targetBranchId, ignoring targetUnitId.

Fix: registered the capability-protected route ahead of :id. Shared eligibility
lookup between listing and submission checks tenant, source branch access, exact
source unit marketSegmentId, another branch, and excludes the source unit.
Missing branch/unit segment configuration returns an actionable error. No broad
US/India guessing. Modal groups eligible results into branches, filters units by
selected branch, resets selection on branch/job changes, ignores stale responses,
and displays request errors. Saves source/target unit IDs and derives the target
branch server-side, rejecting conflicting branch input. Existing cross-branch
delegation restriction and branch-level acceptance behavior retained.

Evidence: frontend tests fail against the original component loaded from Git and
pass against the fix (2 tests). Backend delegation tests pass (4 tests), covering
route/capability, query constraints, invalid source/configuration, forged targets,
and persisted IDs. Full backend: 67 pass / 1 unrelated unit-admin SQL-parameter
expectation failure. Frontend type-check passes. Backend type-check blocked by
missing local @nestjs/throttler module. Diff checks pass.

Status: DONE_WITH_CONCERNS. Local source only; no deployment, schema change, real
delegation sent, or authenticated hosted UI verification. Existing scratch edits
were preserved. Tests use controlled service/Prisma and UI mocks.
