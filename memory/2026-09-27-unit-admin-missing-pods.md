# Unit Admin cannot see existing Bhubneswar pods

User corrected the account email to sahadeb@enfycon.com and clarified that the Pods list is empty, rather than the sidebar or Create Pod user lists.

Confirmed with read-only database queries and existing service methods:
- Sahadeb Barman is active/approved, system role UNIT_ADMIN, assigned to Bhubneswar / Domestic Recuiment, with pod:view, pod:create, pod:edit, pod:delete and pod:reset_cycle.
- Pod 1 (d9026dbd-e941-4fee-aaa3-e9337313ee13) and Pod 2 (3f2c3da3-7b62-40d9-b523-2fadaa6fdc38) belong to the Bhubneswar branch but both have NULL business_unit_id.
- Pod 1 has 3 members; Pod 2 has 6. All linked members and pod heads resolve to Domestic Recuiment (703e5263-a50d-4484-8ad5-d382625b8b87).
- PodsController.findAll defaults UNIT_ADMIN requests to user.businessUnitId. PodsService.findAll then requires an exact businessUnitId. Both existing pods are excluded. Delivery Head requests default to branch scope and can see them.
- The frontend Create Pod payload supplies branchId, not businessUnitId. The service permits NULL businessUnitId, so pods created through a branch-scoped caller can reproduce the missing ownership problem.
- Executing current frontend staff predicates against the actual read-only service responses produced 11 eligible pod heads and 25 recruiter candidates at branch scope; the clarified symptom is the empty pod list.

Root cause: missing unit ownership on stored pods plus inconsistent creation/listing scope. This is not absent Unit Admin pod permissions. Do not broaden Unit Admin visibility to all branch pods as a workaround.

Correction required: associate the two verified pods with the domestic unit and make pod creation persist an explicit validated unit. This investigation did not change application code, records, or production deployment. Prior email-based production verification limitation is resolved by the corrected account email.

Status: investigation complete; repair not yet applied.
