# Company logo storage

The settings API decodes the selected image, validates PNG/JPEG/GIF/WebP with a 2 MB limit, and writes it to `ats_backend/public/image/logos/<tenant UUID>/<SHA-256>.<extension>`. PostgreSQL `ats.tenants.logo_url` stores only `/public/image/logos/...`; the image bytes are not stored in new database saves.

The backend serves that URL directly. A frontend route proxies the same URL so it works on each workspace domain. Content-based filenames give replacements a new cacheable URL. Previous files are retained to keep cached pages and rollback references valid.

Local Docker already bind-mounts `ats_backend` into `/app`. Production blue and green backends both mount `./ats_backend/public/image/logos:/app/public/image/logos`. Back up this host folder together with PostgreSQL. The folder is excluded from Git and image builds; do not remove it during deployments.

## Existing inline logos

Deploy the backend, frontend, and production compose volume changes together **before** migration. Run on the production server that owns the persistent folder, using the active backend container:

```sh
docker exec ats_backend_blue node prisma/migrate-logos.cjs
docker exec ats_backend_blue node prisma/migrate-logos.cjs --apply
```

Use `ats_backend_green` if green is active. The first command is a dry run. The second writes each image, checks the backend URL returns identical bytes, and only then replaces the matching database value. Concurrent edits are protected by a compare-and-swap update. Re-running skips already migrated URLs.

Do not run `--apply` on a developer computer connected to the production database: production would receive links to files that only exist on that computer. Existing data URLs remain readable until migration. For a separate local database, the equivalent container is `ats_backend_dev`.

Validation: `npm test -- --runInBand`; `node prisma/branding-prisma-check.cjs --verify-http` (rolls back database test values); frontend `node --test tests/logo-save.test.cjs tests/tenant-branding.test.cjs` and `npx tsc --noEmit --incremental false`.
