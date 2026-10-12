# System Design Proposal

## Current Architecture Context

Requirement: tenants choose how system-generated emails are sent using their existing workspace email strategy. When no tenant sender is configured, use `EnfySync <no-reply@enfyjobs.com>` through Brevo. This supersedes the earlier proposal to force the platform sender for every tenant. The user's `no-eply` spelling is interpreted as `no-reply`.

`AuthEmailService.sendWelcomeEmail` uses platform SMTP with `SMTP_FROM` or a tenant subdomain sender. `sendMemberCredentialsEmail` first looks up a tenant-connected Microsoft/SMTP account, then falls back to platform SMTP. Consequently, setting SMTP_FROM alone does not enforce the requested sender for all account emails.

`EmailService.sendTenantEmail` independently supports tenant mail strategies. Recruitment mail must retain its tenant-selected sender. Keycloak can send authentication emails separately; the checked-in realm import has an empty smtpServer object. Live realm configuration has not been inspected.

## Proposed Solution

### Brevo Transactional API Integration

Use `POST https://api.brevo.com/v3/smtp/email` with the backend-only `api-key` header. The provided EmailCampaignsApi example creates marketing campaigns; system events instead send directly to a recipient using `sender`, `to`, `subject`, and `htmlContent`. No contact lists or schedules are needed. Use the backend's existing Axios dependency with a typed request/response contract, a finite timeout, and sanitized error handling; no additional SDK dependency is required.

Proposed backend configuration:

```dotenv
BREVO_APIKEY=<secret provided through deployment configuration>
SYSTEM_EMAIL_FROM=no-reply@enfyjobs.com
SYSTEM_EMAIL_FROM_NAME=EnfySync
```

Reuse the user's actual secret variable name if it differs after confirming it; never print its value. The inspected local `ats_backend/.env` did not show a variable named BREVO_APIKEY, SYSTEM_EMAIL_FROM, or SMTP_FROM. The deployment environment may differ and has not been verified. An API key being present alone does not activate delivery without application integration.

The dispatcher will report Brevo acceptance only after a successful response with a message ID. Acceptance is not proof of delivery. Provider rejection, timeout, or quota exhaustion must produce a sanitized failure; do not silently switch sender/provider. No automatic retries on ambiguous timeouts in this initial integration, to avoid duplicate invitations. Free-plan quotas apply to all tenants combined; surface quota failures through sanitized operational logs.

Brevo sender/domain authentication and transactional account activation must be confirmed before a controlled delivery test. Do not make a live sending call during design review.

Keycloak cannot use the Brevo HTTP API through its standard realm SMTP settings. Realm SMTP settings are shared across users of that realm; do not change them per tenant request, which could send another tenant's mail with the wrong identity. Its built-in authentication emails can use platform Brevo SMTP with a separate SMTP key and TLS. Achieving tenant-selectable senders for these messages requires a tenant-aware Keycloak email provider or moving supported email flows into the backend. Inspect current authentication flows and decide that integration before promising tenant-selectable Keycloak emails. Keep secrets outside tracked realm templates.

Official references: https://developers.brevo.com/reference/send-transac-email and https://developers.brevo.com/docs/smtp-integration.

- Introduce a backend-only system mail dispatcher that resolves the tenant's existing emailDispatchMode and validated sender configuration. The platform default is configured through SYSTEM_EMAIL_FROM and SYSTEM_EMAIL_FROM_NAME as `EnfySync <no-reply@enfyjobs.com>`, delivered through Brevo.
- Route welcome, member account, and tenant onboarding mail through this dispatcher. Inventory other system mail producers before implementation and include authentication/security messages in the same sender policy.
- Reuse the existing workspace strategy: default/platform means the shared Brevo sender; direct account means the explicitly selected active default Microsoft/SMTP account; custom domain means the tenant's verified and provider-authorized domain. Do not implicitly choose the newest mailbox or let an unrelated recruitment mailbox connection override the chosen strategy.
- When no custom tenant sender has been configured, resolve to the shared platform sender. A partial, invalid, revoked, or failed explicitly selected configuration is an actionable error, not permission to silently switch to the platform sender. Settings mutations must validate readiness before activating a custom strategy. Missing tenant identity is an error, never a reason to use another tenant or fabricate a default tenant.
- Existing custom domain dispatch does not check customEmailDomainVerified in the inspected sending branch. Require actual provider/domain verification before sending; audit the verification mechanism rather than trusting a display-only flag. Custom-domain Brevo support also requires the domain to be authorized in Brevo, with accurate instructions for that provider.
- Keep tenant context in the subject, template, and validated workspace links. Use only a configured, monitored Reply-To address when replies are supported; do not synthesize tenant admin addresses.
- Account creation and onboarding before any sender setup use the shared platform sender. Subsequent account invitations and notifications follow the tenant's active configuration. Keycloak integration follows the constraints described above.
- Preserve tenant-selected sending strategies for recruitment campaigns and candidate correspondence.
- Surface dispatch failures accurately; absence of production mail configuration must not be reported as delivery success. Reuse any existing retry mechanism, and prevent duplicate delivery when adding retries.

### Database and API Contracts

Reuse the existing tenant strategy, custom domain fields, and email account records; no initial database migration or new public route is proposed. Existing settings and test responses must describe the effective sender accurately and return a typed readiness/error state. Preserve legacy DEFAULT_SUBDOMAIN values internally if needed, but resolve their default sender to the shared platform address. Existing UI options can be retained; displayed default sender and copy must reflect the shared address during implementation. No new layout is proposed by this backend routing proposal. Platform credentials remain accessible only to authorized platform operators. Tenant identity continues to come from trusted backend context.

### Deployment Prerequisites

The chosen provider must authorize `enfyjobs.com` and the configured sender; apply the provider's required DNS authentication records. A relay-based sender does not require a receiving mailbox. Provider credentials remain in secret configuration. Do not expose them in this document, client code, or logs. Production configuration is not verified by this proposal.

## Security & Performance Audit

- [ ] Backend authorization and tenant ownership remain enforced at existing account/onboarding entry points.
- [ ] Tenant credentials are loaded only for the authorized tenant's selected account; secrets and raw database data never reach clients.
- [ ] Sender and Reply-To derive from validated platform or tenant-owned configuration; no arbitrary client-supplied From or hardcoded tenant fallback.
- [ ] Tenant workspace URLs and recipients retain the correct tenant context.
- [ ] A reusable HTTP client avoids per-message setup; select only required tenant fields and query accounts only for direct-account mode.
- [ ] No added frontend calls, N+1 queries, duplicated tenant configuration, or schema expansion.
- [ ] Errors are sanitized; logs exclude secrets, invitation tokens, and message bodies.
- [ ] Missing configuration and provider rejection do not yield false delivery success.

These are implementation acceptance criteria, not claims of completed validation.

## Validation Plan

Verify a new tenant with no sender setup uses the shared Brevo sender; a configured direct-account tenant uses its selected mailbox; and a verified custom-domain tenant uses its authorized sender. A connected mailbox with platform mode selected must not override the platform sender. Test partial/unverified settings, expired credentials, provider failures, missing tenant identity, cross-tenant access, and absence of silent fallback. Verify recruitment mail still uses its configured tenant strategy. Mock Brevo requests to check the API-key header, sender, recipient, accepted message ID, missing platform configuration, rejection, quota errors, and timeouts without exposing credentials. Run backend build and focused tests. Validate delivered From headers and domain authentication using controlled recipients after implementation. Test Keycloak-generated messages separately and explicitly document whether tenant-aware sending has been implemented.

## Approval Status

Approved by the user and implemented for backend account/invitation/onboarding events and the existing email settings screen. Brevo uses BREVO_APIKEY. Tenant selection, real custom-domain ownership/provider verification, sanitized failures, granular settings authorization, and secure Microsoft connection state/PKCE are implemented. Account responses report email acceptance/failure independently of saved account status. Repeated approval requests do not duplicate onboarding email.

Validation: 66 focused email/authentication tests passed, backend and frontend type checking passed, and the generated API contract is synchronized. Read-only Brevo account/domain/sender checks returned HTTP 401; the configured API key needs correction before live validation. Production deployment and live delivery/domain authentication have not been verified. Keycloak authentication mail remains separately configured, as described in docs/brevo-system-email-setup.md.
