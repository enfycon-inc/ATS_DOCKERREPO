# Audit & Fixing Plan — C2H Client Bill Rate

## Executive summary

The C2H client bill-rate **amount is included in the job-posting payload and persisted** when a rate is entered. The API maps the amount, currency, and term into dedicated job fields. The rate is required when publishing a job.

There is a confirmed unit-handling defect: the C2H form lets the user choose **Monthly** or **Hourly**, but submission formatting ignores that selection and derives the unit from job type. C2H is always serialized as `/mo`. An hourly bill rate is therefore saved as monthly. This does not explain a missing amount: the screenshot’s `N/A` indicates that the inspected job has no numeric client bill-rate value available to display. Static code review cannot confirm what was actually stored for that specific job without read-only access to its API/database record.

## Evidence and data flow

1. The India staffing form requires `clientBillRate` for submission: `ats_frontend_main/app/(dashboard)/job-posting/new/IndiaStaffingForm.tsx:87`.
2. For non-permanent jobs, including C2H, the form shows a client bill-rate input and a Monthly/Hourly selector: `.../IndiaStaffingForm.tsx:2567-2589`.
3. The selector writes to `billUnit`, but the submit handler calls `indiaBudget(data.clientBillRate, "", data.jobType)` without passing `billUnit`: `.../IndiaStaffingForm.tsx:1303-1309`.
4. `indiaBudget` chooses `/mo` based on job type (`Contract`, `C2H`, `Freelance`) and cannot represent the selected hourly unit: `ats_frontend_main/lib/india-job-commercials.ts:1,15-23`.
5. The resulting value is sent as `clientBillRate` in the create/update payload: `.../IndiaStaffingForm.tsx:1425-1431,1467-1470`.
6. The backend parses that field into `clientBillRateMin/Max`, `clientBillCurrency`, `clientBillTerm`, and `placementCommissionPct`: `ats_backend/src/jobs/job-commercials.ts:9-43`.
7. Job creation spreads those fields into the persisted Prisma job data: `ats_backend/src/jobs/jobs.service.ts:1132-1151`; the transaction creates the job at `.../jobs.service.ts:1214-1215`. Updates also apply the parsed fields: `.../jobs.service.ts:2470-2475`.
8. The database model has separate client bill-rate amount, currency, and term fields: `ats_backend/prisma/schema.prisma:916-920`.

## What this means for the reported job

The screenshot shows a C2H job with pay rate `INR - 80000 to 100000 /mo` and client bill rate `N/A`. Pay rate and client bill rate are separate fields; the backend does not infer one from the other. If no numeric client bill rate was submitted or stored, the UI correctly shows `N/A`. If an hourly rate was entered, current code would store it with a Monthly term, but should still retain its numeric amount.

To prove the specific job’s saved values, inspect its read-only API/database record for `client_bill_rate_min`, `client_bill_rate_max`, `client_bill_currency`, `client_bill_term`, and `placement_commission_pct`. No live database/API record was available during this audit, so this plan does not claim the screenshot’s exact persisted row was independently queried.

## Proposed implementation

1. Update the India commercial-rate formatter to accept an explicit unit for bill rates, while retaining the existing job-type-based unit for pay rates.
2. Format C2H/Contract/Freelance bill rates using the selected `billUnit`; keep candidate pay rates monthly for these job types.
3. Preserve Permanent placement commission formatting and all existing permission-controlled display behavior.
4. Confirm API parsing already accepts both `/mo` and `/hr`; no database schema change is expected.
5. Review the affected create, draft-publish, and edit paths for consistent bill-rate unit serialization.

## Impact and edge cases

- C2H with monthly bill rate and monthly pay: both values should persist with their own amount and Monthly term.
- C2H with hourly bill rate and monthly pay: bill rate should persist as Hourly while pay remains Monthly.
- Permanent job with placement commission: percentage should remain in the commission field, with no numeric bill rate fabricated.
- Draft saved without a bill rate: draft may remain incomplete; publishing must continue requiring the bill rate.
- Editing a job without changing its rate: omitted rate fields should not overwrite the existing persisted value; an explicitly updated rate should update amount and term together.

## Rollback

If the change causes unexpected values, revert only the formatter and form call-site update. Existing persisted rates and schema fields remain unchanged; no data migration is required.

## Verification after approval

Verify the UI payload and persisted/read-back fields for monthly and hourly C2H rates, confirm pay remains monthly, confirm Permanent commission behavior, and confirm draft publishing validation. No verification commands or tests were run during this read-only audit.
