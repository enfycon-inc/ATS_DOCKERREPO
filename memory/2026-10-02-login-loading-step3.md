# Login hydration: third focused fix

- User authorized continuation after the loading-screen fix.
- Symptom: React hydration warnings on the login page; tenant/global sign-in options could flicker while the form was rebuilt.
- Root cause: `LoginForm` called `getTenantIdentifier()` during render. The server has no browser host and returned the global-domain result, while the browser returned the tenant result.
- Change: hostname-dependent portal detection now waits for client mount. The first server and browser render are deterministic; tenant-specific options are enabled after hydration.
- Validation: login-navigation and navigation-bootstrap focused tests pass (8/8); diff whitespace check passes. TypeScript no-emit was started but did not finish within the local command window and was stopped without output.
- Tradeoff: tenant social options appear after hydration/policy loading rather than being guessed during SSR; this removes the hydration rebuild and is the safe behavior.
- Status: DONE_WITH_CONCERNS — focused tests pass; browser console verification still recommended.
