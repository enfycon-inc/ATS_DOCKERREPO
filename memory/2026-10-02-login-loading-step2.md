# Login loading: second focused fix

- User confirmed the first spinner fix works and authorized the next fix.
- Symptom: blank screen between the login document and dashboard content.
- Root cause: dashboard route fallback returned null; root fallback rendered nothing on the server and hid itself after five seconds regardless of completion.
- Change: shared server-rendered workspace progress component. Root fallback fills the screen; dashboard fallback stays within content so existing navigation remains available. No client timers; route boundary controls lifetime. Includes status/live/busy semantics and reduced-motion support.
- Regression evidence: rendering both original fallbacks produced empty HTML and failed the two visibility tests. After the change, all 11 focused route-loading, login-navigation, and navigation-bootstrap tests pass. TypeScript no-emit check passes.
- Scope: loading presentation only. No authentication, permission, session, query, or redirect behavior changed. Earlier login-navigation work retained.
- Limits: authenticated end-to-end visual confirmation still needed. Actual request latency and the other audit findings remain subsequent work. Broader suite contains existing unrelated failures documented in step 1.
- Status: DONE_WITH_CONCERNS — regression tests and types verified; live authenticated transition not recorded.
