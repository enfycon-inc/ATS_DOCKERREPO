# Pod-first job assignment

Approved workflow: assign a posted job to a pod, then let its lead allocate individual recruiters. Pod membership alone does not authorize submissions. Emergency overrides stay in the actor's current unit and require a reason.

## Configure existing roles

Open **Role Management → edit the role → Jobs Management** and save the appropriate checkboxes. Changes apply to the selected active role; a role name alone grants no allocation authority.

| Role | Enable | Leave disabled |
| --- | --- | --- |
| Pod Lead | `job:view`, `job:assign_recruiter` | `job:override_assignment`; optionally both whole-pod access permissions |
| Recruiter — individually allocated work | `job:view`, `submission:create` | `job:view_pod_jobs`, `job:submit_pod_jobs`, assignment permissions |
| Delivery Head — emergency allocation | `job:view`, `job:assign_pod`, `job:assign_recruiter`, `job:override_assignment` | No permissions grant access outside the current unit |
| Job author | `job:create`, `job:assign_pod` | `job:override_assignment` for normal posting |

The pod's lead must be configured on the pod record. Enabling `job:assign_recruiter` does not let an ordinary pod member allocate work: the backend verifies actual pod leadership and the job-to-pod mapping, then validates every selected recruiter against that pod.

## Optional whole-pod work mode

- `job:view_pod_jobs`: pod members may view all jobs mapped to their own pod, but cannot submit without individual allocation.
- `job:submit_pod_jobs`: with `submission:create`, pod members may submit to jobs mapped to their own pod without individual allocation. This also exposes those jobs in the sourcing list.
- Disable both to restore individual-allocation-only work for recruiters. Existing direct allocations continue to authorize submission.

These options are available in role permission ceilings but are not automatically granted to saved roles. Review existing roles before rollout; Pod Leads that previously relied on their role label must now receive the explicit assignment capability.

## Emergency allocation

Direct assignment while posting requires `job:override_assignment` plus recruiter-assignment permission. Enter the emergency reason in the job form. Existing-job assignment has a reason field in its allocation dialog. Assignments validate the current unit and selected resources; override events are recorded in the audit log. Existing unit policy still applies, including whether direct-recruiter assignment is enabled.

## Enforcement

- Job listings and detail access distinguish pod leadership, optional whole-pod visibility, and direct recruiter allocation.
- Submission creation validates `submission:create`, the authenticated submitting identity, current active membership, job ownership scope, and direct allocation or explicit whole-pod submission capability.
- A pod lead's recruiter changes preserve allocations belonging to other pods mapped to the same job.
- Existing draft and market-specific job forms retain their workflows; normal authors see pod allocation instead of emergency recruiter allocation.

## Verification

Focused tests cover direct allocation, disabled/enabled pod submission, view-only pod access, spoofed submitting identities, missing assignments, foreign jobs, per-recruiter staffing checks, and permission-based lead allocation. Live authenticated UI verification remains required before treating this as production-verified.

Validation completed: 255 backend tests across 24 suites, 15 frontend tests, backend and frontend production builds, and frontend type checking passed.
