# Sidebar flicker while switching dashboards

Reviewed the supplied 26.87-second recording through extracted frames. Each switch briefly rendered the new dashboard, then cleared the sidebar and showed a loading dashboard before the menu returned. Source confirmed that ProfileDropdownNav dispatched the role change and then assigned window.location.href, reloading the document. Sidebar and top navigation also committed profile and role metadata independently during mount.

Changed the profile switch to Next client-side router navigation, preserving the mounted layout and loaded sidebar data. Profile and role definitions now commit together in navigation, with an unmount cancellation guard.

Eight tests pass, including the existing five role-selection tests and three new callback tests. New tests execute the production switch callback and reject document navigation, verify role persistence/events, and hold the role response pending to check neither navigation component renders a profile prematurely. Authenticated browser verification and deployment were not performed.
