# Sidebar hard-refresh rendering

Reviewed the nine-second recording via extracted frames. Hard refresh rendered an empty navigation shell before the browser fetched profile and role definitions. The earlier client-router change fixed role switching but did not initialize server-rendered navigation.

Added request-local authenticated server loading of profile and role definitions with an eight-second abort and no shared caching. The layout passes a complete snapshot to the sidebar; the initial server render and browser hydration use the same selection, with no duplicate initial fetch. Existing client loading remains a fallback for server failure. Saved role IDs are mirrored in a scoped SameSite cookie, validated against assignments by the existing selector, and old browser-only preferences migrate on load. Restored the existing sidebar expansion cookie. Permissions are unchanged.

Fourteen focused tests passed: navigation bootstrap and failure behavior, no refetch on seeded sidebar mount, stable hydration selection, scoped server-readable cookie persistence, and earlier role/switch regressions. Frontend type checking passed. Live authenticated browser verification has not been performed.
