# Multi-role login dashboard mismatch

The profile dropdown selected an assigned role using the profile role ID. The dashboard independently selected `systemRole` or the first role, rendered before the role catalog loaded, and requested a different catalog (without includeSystem). Navigation used stale login-session fields. Saved overrides were also validated differently by each component. This allowed the label and rendered dashboard to disagree.

Added a shared dashboard-role selector used by the dashboard, profile dropdown, sidebar, and top navigation. It validates saved switches against assigned IDs, uses the live profile's selected role ID by default, and derives label and archetype from the same record. New switches save IDs rather than names. The dashboard waits for definitions before rendering; navigation fetches the live profile. Existing capability enforcement is unchanged. No account assignments or database values were changed for this issue.

Validation: five regression tests passed (first login with conflicting metadata, switching, invalid override, legacy names, duplicate names). Frontend TypeScript check and diff whitespace check passed. Changes are local; deployment and authenticated verification on deb.enfyjobs.com were not performed.
