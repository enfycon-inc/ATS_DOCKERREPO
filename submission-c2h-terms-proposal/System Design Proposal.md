# System Design Proposal — C2H Client Terms in the submission table

## Current architecture context

- The submission list SQL selects `client_bill_rate_min`, `client_bill_rate_max`, `client_bill_currency`, `client_bill_term`, and `placement_commission_pct` from the job.
- `mapRowToDetails` sends bill-rate fields only when the viewer has `job:bill_rate:view` (or a global permission), and sends `clientCommissionPct` only with `placement:view` (or a global permission).
- The table’s `formatClientTerms` displays a percentage when the API returns a permitted commission; otherwise it formats the permitted bill rate. If the API returns neither, it displays an em dash.
- C2H is a recognized contractual job type elsewhere in compensation code, but the terms formatter does not derive terms from `jobType`. Correctly so: job type alone does not say whether the client pays a monthly/hourly rate or placement commission.
- The screenshot alone does not reveal the saved commercial fields on the specific QA Testing job or the active user's effective permissions. Therefore the precise cause for that row could be (a) a percentage saved without the viewer's `placement:view` permission, (b) no client rate/commission saved, or (c) an input-to-storage mapping issue.

## Proposed solution

### Display behavior

Keep the existing single **Client terms** column and render only a client term the viewer is permitted to see:

1. If a percentage commission is saved and the viewer has `placement:view`, display it as text, e.g. `8.33% placement commission`.
2. Otherwise, if a monthly/hourly (or other saved) client bill rate exists and the viewer has `job:bill_rate:view`, show its amount and unit, e.g. `INR 1,200 / hour` or `INR 80,000 / month`.
3. If both values exist and the viewer has both permissions, apply the existing agreed precedence of percentage first; do not introduce a second column.
4. If the only populated value is not permitted, or neither value is saved, display `—`. Never infer client terms from candidate pay/current or expected compensation.

### Diagnosis and implementation path

- Confirm the C2H job’s saved `client_bill_rate_*` and `placement_commission_pct` values through an authorized job record/detail view (avoid adding raw financial values to logs).
- Confirm the viewer's effective `job:bill_rate:view` and `placement:view` permissions through the existing permission context.
- If the job has a monthly/hourly rate but its term is missing or incorrectly mapped, repair the existing job-write/read mapping and render the saved rate and unit.
- If it has only a percentage, retain the permission boundary; grant `placement:view` only through the normal RBAC configuration for staff intended to see placement economics. Recruiters without that permission continue to see no commission.
- If neither client field is saved, the UI must continue to show `—`; update the job through the normal authorized edit flow rather than guessing a value.

No schema change is proposed. Keep the backend response permission-filtered and keep the UI column available only when at least one relevant permission exists.

## API and UI touchpoints

- Backend list projection and `mapRowToDetails` in `ats_backend/src/recruiter-submissions/recruiter-submissions.service.ts`.
- Commercial parsing and storage in `ats_backend/src/jobs/job-commercials.ts` and the existing job create/update path, only if the saved record confirms a mapping defect.
- Single-column formatting in `ats_frontend_main/lib/submission-compensation.ts` and table cell rendering in `ats_frontend_main/app/(dashboard)/utility/submissions/page.tsx`.
- Keep permission checks on the API; hiding a field in the browser is not an authorization boundary.

## Security and performance audit

- [x] No commission is returned without `placement:view` (or the existing global grants).
- [x] No bill rate is returned without `job:bill_rate:view` (or the existing global grants).
- [x] Do not derive or expose client terms from candidate compensation fields.
- [x] Existing single list request and selected SQL fields are sufficient; no extra per-row request or schema fields are needed.
- [x] If a data-mapping correction is required, preserve the normalized rate/term fields already in the job schema.
- [ ] During implementation, verify a C2H record with a bill rate, a commission-only record, and a record with no saved terms using authorized test fixtures; verify restricted permissions receive no commission data.

## Preview limitation

The image-generation tool is not available in this session. The attached preview is a native UI mockup rather than a photo-rendered image. It illustrates the agreed single-column text treatment and permission-dependent values.

## Approval checkpoint

Do you approve this system design proposal? Should I proceed with the implementation?
