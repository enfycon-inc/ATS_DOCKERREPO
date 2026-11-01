# Audit & Fixing Plan — Client Terms Label

## Executive summary

The database design is appropriate: fixed client rates are stored with identical minimum and maximum values, ranges can use both bounds, and permanent placement commission has a dedicated field. The recruiter submission table already presents these alternatives in one **Client terms** column. The job-posting table still uses market-specific labels (“Client Bill Rate / CTC” or “Client Bill Rate / Salary”), even though its value can also be a placement commission. This is a presentation inconsistency, not a schema defect.

## Root cause

- `ats_frontend_main/app/(dashboard)/job-posting/components/job-posting-dashboard.tsx:359-366` labels the client commercial column by market as “Client Bill Rate / CTC” or “Client Bill Rate / Salary”. The row renderer uses the unified `job.clientBillRate` value.
- `ats_frontend_main/app/(dashboard)/job-posting/components/data-table/job-table-row.tsx:527-537` renders that value, which may be a numeric rate, range, or commission text.
- `ats_frontend_main/components/submissions/tracker-columns.tsx:8-12,67` already defines a single “Client terms” column for submissions.
- Rate storage is already normalized by `ats_backend/src/jobs/job-commercials.ts:31-43`; this change does not need database or API changes.

## Impact radius

- Job-posting list header and its column chooser will use the clearer umbrella label.
- Submission table already uses “Client terms” and requires no change.
- Existing permission gating, stored rate values, ranges, permanent commissions, and recruiter visibility rules will remain unchanged.

## Implementation plan

1. Change the job-posting client commercial column label to **Client terms** in `job-posting-dashboard.tsx`.
2. Keep the existing `clientBillRate` data path and rendering logic so fixed rates, ranges, and placement commission text display as saved.
3. Keep visibility gating unchanged; this work only changes the label.
4. Review the rendered label in both the table header and column chooser to confirm they share the updated column definition.

## Edge cases

- Permanent job displays its percentage placement fee under “Client terms”.
- Contract/C2H job displays a monthly or hourly bill rate under the same label.
- A range remains formatted with both minimum and maximum amounts.
- Users without existing permission continue to see the same columns and values as before.

## Rollback plan

Revert the single column-label change in `job-posting-dashboard.tsx`. No data migration, API change, or rollback of stored records is needed.

## Verification

After approval, inspect the shared column definition and run the repository’s relevant type/build check only if requested. No code or data has been changed for this plan.
