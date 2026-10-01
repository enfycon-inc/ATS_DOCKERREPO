# Login loading, step 5: share the server session read

The user authorized the next focused login fix. Dashboard metadata and the parent
layout separately called auth(). Navigation bootstrap already uses React cache,
so a second profile network request was not established by those two call sites.

Wrapped getSessionSafe in React cache so metadata and layout share the same
request-scoped result, including any token refresh. Cleared the deadline in
finally. Preserved the eight-second timeout and existing login/tenant redirects.
This is request-local memoization, not a persistent cache of user sessions.

Added behavioral tests loading the real layout with mocked request-scoped React
cache, auth, headers, and timers. All three failed before the change and passed
afterward. All 16 focused login/loading/bootstrap tests passed. The broader suite
still reports failures in existing branch settings/navigation permissions,
Microsoft button source expectations, and unit-admin tests. Diff whitespace
check and TypeScript check passed. No authenticated end-to-end timing was taken in this step, and
no specific latency reduction is claimed.
