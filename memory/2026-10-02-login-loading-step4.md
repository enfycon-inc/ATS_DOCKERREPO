# Dashboard bootstrap: fourth focused fix

- Symptom: dashboard loading remained slow despite parent layout already fetching workspace navigation.
- Root cause: the parent dashboard layout loaded session/profile/navigation, while the nested `/dashboard` layout independently loaded `auth()` and the same navigation again. This duplicated authenticated profile/role requests during initial dashboard navigation.
- Change: mounted `DashboardProvider` once in `ClientRoot` using the parent layout's `initialNavigation`; nested dashboard layout is now a transparent route boundary.
- Validation: 10 focused tests pass, including ownership checks proving the nested layout no longer calls auth/bootstrap, plus previous login/loading tests. Diff whitespace check passes.
- Scope: removes duplicate bootstrap work; no API contract, auth policy, or permission logic changed.
- Remaining timing work: `generateMetadata()` also calls navigation bootstrap during page rendering and should be measured/optimized separately; dashboard widgets still fetch their own data after the shell is ready.
- Status: DONE_WITH_CONCERNS — duplicate route bootstrap removed and tested; live request timing still needed.
