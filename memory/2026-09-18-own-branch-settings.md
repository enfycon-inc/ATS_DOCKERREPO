# Own-branch settings page

The branch settings route previously loaded the entire tenant directory and hierarchy, then hid branches in the browser. It exposed branch totals and directory controls unnecessarily. Detail/member read endpoints and branch remark mutations lacked complete ownership checks.

Branch-scoped users now load their live assigned branch only and get the existing settings form inline with Add / Manage Remarks. Tenant administrators retain the directory. Removed UI role-name overrides from permission resolution. Branch list/detail/member/hierarchy reads are scoped, and branch remark reads/creation/deletion enforce ownership and editing capabilities. Job delegation uses a separate capability-protected endpoint returning IDs/names only, preserving co-sourcing without exposing settings or staff.

The full 22-test backend suite passed; two additional remarks-read tests were then added and the six-test remarks suite passed. Frontend type checking and the settings-loader regression passed, verifying no directory/hierarchy fetch for a branch admin. Backend and frontend production builds passed (frontend required network access for its existing Google Font). No real branch settings or remarks were modified during validation. Authenticated browser verification and deployment were not performed.
