# Company branding save failure

- Symptom: PATCH /api/auth/tenants/my-settings returned HTTP 500 when saving logo and browser title.
- Root cause: recent branding code/schema change did not migrate the running database. Both ats.tenants.site_title and logo_url were absent. PostgreSQL reported 42703 for site_title. The schema also limited logo_url to 2048 characters although the UI uploads base64 data URLs.
- Fix: added targeted, idempotent ats_backend/prisma/branding.sql and applied it to the running backend database. Updated Prisma logoUrl to Text.
- Regression: ats_backend/prisma/branding-check.cjs --verify calls the running compiled AuthTenantService in a transaction, saves a title and 10,000-character logo payload, checks the returned values, then rolls back. It failed with the original missing-column error before migration and passed afterward. --apply applies the migration first.
- Evidence: both columns verified in information_schema; service round-trip passed. All 7 backend Jest suites / 26 tests passed locally.
- Verification limit: checked the running service/database path; did not perform an authenticated browser save. No existing company branding values were changed by the test.
- Status: DONE_WITH_CONCERNS (browser verification not performed).

## Follow-up: failure on both local and hosted site

- User reported continued failure on deb.localhost:3000 and deb.enfyjobs.com.
- Full PrismaService -> AuthQueryService -> AuthTenantService rollback test reproduced PostgreSQL 22001: value too long for character varying(2048).
- Fresh information_schema inspection showed logo_url had reverted from TEXT to VARCHAR(2048) since the earlier successful migration/test. Production Dockerfile runs prisma db push on every start; the deployed schema can therefore restore the old limit. The specific process that reverted the column was not observed.
- Reapplied the targeted migration and verified the full Prisma path plus JSON serialization successfully, including company name, title and a 10,000-character data URL. Test values rolled back.
- Added prisma/branding-prisma-check.cjs as the full-path regression check. The local schema correction to @db.Text must be included in deployment to prevent future startup schema sync from restoring the limit.
- No connected browser was available for authenticated UI verification; production process/deployment was not changed.

## Follow-up: branding lost on refresh / header unchanged

- Root cause: getProfile omitted tenant site_title/logo_url, NavbarLogo used only hardcoded platform assets, and the company save handler only assigned document.title temporarily.
- Fix: profile now returns tenant.siteTitle and tenant.logoUrl; authenticated dashboard metadata uses the saved title; shared TenantBrandingProvider initializes from the request-local profile and updates the header/title after saves. A profile fetch fallback handles missing server bootstrap. Default platform branding remains the fallback when custom branding is empty.
- Verification: backend build passed, all 8 suites / 27 tests passed, frontend TypeScript check passed. Real Prisma transaction saved branding and confirmed a fresh AuthUserService.getProfile returned both values, then rolled back. Local backend rebuilt and restarted.
- Regression tests: auth-branding.spec.ts and expanded prisma/branding-prisma-check.cjs.
- Limitation: no connected authenticated browser for visual verification; hosted frontend/backend code still requires deployment.

## Follow-up: persisted branding loaded in form but shell still defaults

- Read-only inspection of the actual deb tenant found site_title = `deb technology`, logo_url length = 117434 characters, updated_at = 2026-09-23T16:53:43.687Z. Fresh getProfile for the affected member returned the same title and logo length. Data is saved; this is a frontend reload problem.
- Next development log shows the dashboard receiving initialNavigation=null. The branding provider relied on a separate session-token fetch, skipped loading without that token, and trusted even partial initial branding. Meanwhile the settings form successfully loaded via atsApi.auth.me but only published branding to the shared context when Save was clicked.
- Changed provider to revalidate via the same authentication-aware API client as the form, including partial-bootstrap cases. Form profile loading now publishes the returned tenant branding to the shell. A revision guard prevents a late profile fetch from replacing newly saved branding.
- Added frontend tests/tenant-branding.test.cjs covering absent session/bootstrap, partial branding, and a delayed response racing a save. Frontend TypeScript check passed. Full frontend suite: 18 passed, 13 failed in existing navigation/permissions tests (no changes to those modules in this task).
- No browser/app surface is connected for UI verification. Local dev frontend picks up these source changes; no backend restart or database edits needed for this follow-up.

## Store logo files with database links

- User requested server folder `/public/image/logos` and image links in PostgreSQL.
- Implemented backend conversion on the existing authenticated settings save: validate raster image (PNG/JPEG/GIF/WebP, max 2 MB), write bytes atomically into `ats_backend/public/image/logos/<tenant>/<sha256>.<ext>`, and store only its `/public/image/logos/...` path. Save response is now the source of form/header state.
- Backend serves files with immutable cache headers and nosniff. Frontend proxy route serves the same URLs on workspace domains, with the specific public logo path exempted from login middleware. Existing inline logos remain readable until migration.
- Production blue/green services share a bind-mounted logo folder. Git/build ignore files exclude runtime images. Deployment and migration instructions: docs/company-logo-storage.md.
- Added read-only-by-default prisma/migrate-logos.cjs. Applying verifies file HTTP bytes before replacing matching inline DB data. Dry run found one inline logo (deb, 117434 chars). Did not apply on the developer computer because the database is shared with hosted production and files would only exist locally. Deployment timing question was offered; no answer received during implementation, so migration was prepared for next deployment.
- Verification: backend build, all 9 suites / 30 tests passed; focused frontend tests 4/4 passed; frontend typecheck passed before final proxy exemption and rerun after it. Full Prisma save/profile read and HTTP image-byte comparison passed with DB rollback. Workspace URL at Host deb.localhost:3000 returned HTTP 200 image/png, 68 bytes, immutable caching. Production compose config validated. Local backend rebuilt/restarted; no hosted deployment performed.

## Logo sizing and upload guidance

- Actual saved PNG is 858 x 291; alpha bounds are x=36, y=44, width=789, height=147. Previous full-canvas 32px rendering made the artwork only about 16px tall.
- Added shared CompanyLogoImage renderer that measures transparent bounds with a bounded canvas and displays the original image through an SVG viewBox. Header and preview fit the visible artwork at up to 240 x 34px without changing stored image bytes. For this logo, computed artwork height increases to 34px.
- Upload guidance recommends 480 x 96px (5:1), transparent/tightly cropped artwork, light lettering on the blue header, accepted formats and the 2MB limit. Shows actual uploaded dimensions plus a blue header preview. Adjusted layout to stack on narrower screens and made upload control keyboard accessible.
- Six focused branding/logo tests passed; frontend TypeScript check passed. Added logo-bounds regression tests for transparent margins and opaque/empty images. No connected browser for final visual verification.
