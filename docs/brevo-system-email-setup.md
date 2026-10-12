# Brevo system email setup

## Platform configuration

Configure these values in the backend deployment environment. Do not commit the real API key.

```dotenv
BREVO_APIKEY=<private Brevo API key>
SYSTEM_EMAIL_FROM=no-reply@enfyjobs.com
SYSTEM_EMAIL_FROM_NAME=EnfySync
FRONTEND_URL=https://enfyjobs.com
BASE_DOMAIN=enfyjobs.com
```

The backend uses the transactional endpoint, not Brevo marketing campaigns. Authenticate `enfyjobs.com` and authorize the sender in Brevo. Ensure transactional sending is enabled for the account and authorize the server IP if Brevo requires it. Redeploy the backend with the new environment. A key alone does not verify the sender or domain.

## Tenant choices

Workspace administrators with `tenant:settings` or `tenant:manage` (or a platform capability) manage the existing Email Integration screen:

- Platform Default: system emails use the shared sender through Brevo. Legacy DEFAULT_SUBDOMAIN database values now resolve to this address.
- Direct Mail: connect Microsoft 365 or SMTP, explicitly select an active default account, then activate Direct Mail. Microsoft OAuth requires MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, and MICROSOFT_REDIRECT_URI. The connection uses authenticated server identity, a one-use Redis state with a 10-minute lifetime, and PKCE. State is consumed atomically through the queue's Redis script interface.
- Custom Domain: save the domain, publish the workspace ownership TXT plus actual Brevo DNS records displayed, verify ownership and provider authentication, then activate Custom Domain. Domain records are fetched from Brevo; no sample SPF/DKIM strings are treated as real verification. Existing fake verification flags are insufficient: sending also checks workspace DNS ownership and Brevo authentication.

The ownership record is deterministically scoped to the tenant and domain, so another tenant cannot reuse that domain's verification proof. Do not replace an existing DMARC policy without considering its current use; apply provider records through the domain administrator.

An incomplete custom configuration cannot be activated. If an already selected tenant sender fails, the backend reports failure rather than changing sender or claiming delivery. Returning to Platform Default is an explicit administrator choice. Connected recruitment accounts do not override Platform Default.

## Supported system email events

Invitations, member account creation, new tenant registration, platform approval/activation, and manually created tenant onboarding use the shared tenant-aware dispatcher. Onboarding messages contain workspace context and no password. Existing member credential templates remain in use for that flow.

Account/invitation creation responses include emailNotification status (accepted, failed, or disabled where supported). A mail failure does not roll back the saved account or invitation. Test Email reports provider acceptance, not guaranteed inbox delivery. No automatic retries occur after ambiguous timeouts.

## Keycloak authentication emails

Keycloak-generated password reset and verification emails remain separate from the backend dispatcher. Standard realm SMTP settings are shared across tenants and cannot safely be switched for each request.

For platform sending, configure Realm Settings → Email with the same From address and a separate Brevo SMTP key; the API key is not an SMTP password. Use the Brevo-provided SMTP login, server, and TLS settings. Keep credentials outside tracked realm JSON. Tenant-specific Keycloak senders require a custom tenant-aware email provider or an explicitly designed backend authentication-email flow; that integration is not implemented here. The UI describes this limitation rather than promising password-reset routing.

## Validation and limits

Implementation verification on 2026-10-12: 66 focused email/authentication tests passed; backend and frontend TypeScript checks passed; generated API contract synchronization and changed-file whitespace checks passed. The local backend environment contains BREVO_APIKEY and the configured platform sender. An initial read-only Brevo check returned HTTP 401; the user identified an IP authorization block and manually authorized the IPs. After authorization, the account check succeeded and Brevo accepted a requested test email from no-reply@enfyjobs.com to imsahadeb@gmail.com with HTTP 201 on 2026-10-12 (message ID: <202610120743.83264785548@smtp-relay.mailin.fr>). Provider acceptance does not confirm inbox delivery. No production deployment was performed.

Brevo's free quota is shared across tenants. Quota exhaustion returns a sanitized provider failure. Verify the From header and domain authentication with controlled recipients after deployment. One explicitly requested live test email was accepted by Brevo; production Keycloak settings were not changed.

Run `node docs/sync-email-contract.cjs --check` at the parent repository before builds; it fails if the generated frontend contract differs from the backend source. After a contract change, run the same script without --check. The generated frontend copy keeps its Docker build context self-contained.

Official references: [Transactional email API](https://developers.brevo.com/reference/send-transac-email), [Domain authentication](https://developers.brevo.com/docs/domain-authentication-and-verification), [SMTP setup](https://developers.brevo.com/docs/smtp-integration).
