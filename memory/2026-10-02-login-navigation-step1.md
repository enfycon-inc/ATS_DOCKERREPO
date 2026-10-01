# Login navigation: first focused fix

- Scope: user authorized addressing the audited login flow one step at a time; local environment localhost:3000 confirmed.
- Symptom: successful password login reveals the login form again before the dashboard document loads.
- Root cause: `useTransition` completes when `window.location.href` is assigned, before document navigation commits. The loader previously depended only on that transition and SSO state.
- Change: explicit navigation state retains the existing overlay through document unload. Direct tenant login, platform login, and cross-domain handoff use the same navigation callback. A synchronous navigation failure releases the overlay.
- Validation: five production-callback regression tests pass. The original loading condition was evaluated with transition complete/navigation pending and returned false, reproducing the defect. TypeScript no-emit check and git diff whitespace check pass.
- Broader suite: existing failures in untouched branch settings, navigation permissions, unit-admin and Microsoft-login tests. The Microsoft test expects an exact disabled expression that differs from the current social component. No unrelated fixes applied.
- Baseline local HTTP timings: login page 444–712 ms; unauthenticated session 127–326 ms; public tenant auth policy 975–3892 ms. These do not measure credential validation, Keycloak, or authenticated dashboard APIs.
- Limits: a fresh authenticated browser recording has not been captured. This fixes the demonstrated state transition in tests; it does not establish an improved end-to-end loading time. Empty route fallback, hydration mismatch, request waterfall, and timeouts remain subsequent work.
- Status: DONE_WITH_CONCERNS — focused regression verified; browser verification and remaining loading improvements outstanding.
