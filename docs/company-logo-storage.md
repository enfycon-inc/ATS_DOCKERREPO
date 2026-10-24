# Tenant logo storage

Tenant Settings → General has independent Site Logo and Login Page Logo controls. Site Logo continues to serve the application header, emails and password setup. Login Page Logo is used by all sign-in page layouts. Removing either logo does not change the other.

## Dimensions and limits

| Purpose | Recommended source / maximum optimized bounds | Typical display |
| --- | --- | --- |
| Site logo | 480 × 96 px | Header slot up to 240 × 34 px |
| Login logo | Within 360 × 96 px | Up to 180 × 48 px |

New uploads accept PNG, JPEG, static GIF and WebP up to **200 KB each**. The backend decodes with a 16-million-pixel safety limit, rejects animation, preserves aspect ratio/transparency, avoids enlarging images, removes metadata, and encodes WebP. It first tries lossless encoding, then high-quality compression if needed to target **30 KB**. The hard saved-file limit is **50 KB**; images that cannot meet it are rejected rather than silently degraded further.

Images are atomically written to `ats_backend/public/image/logos/<tenant UUID>/<SHA-256>.webp`. PostgreSQL stores only image references in `ats.tenants.logo_url` and `login_logo_url`. Repeated uploads of the same artwork produce the same URL. Both fields update in one settings mutation; invalid input leaves database settings unchanged. Old files are retained for cached pages and rollback.

The backend and frontend proxy serve the permanent paths with one-year immutable caching. New content gets a new filename. Production blue and green backends share `./ats_backend/public/image/logos:/app/public/image/logos`. Back up that folder with PostgreSQL; do not remove it during deployments.

## Deployment and existing logos

1. Back up PostgreSQL and the persistent logo folder.
2. Apply the checked-in Prisma migration with `npm run db:migrate:deploy` from the backend deployment environment. It adds the optional login-logo column and copies existing site-logo references once, preserving initial branding without duplicating files.
3. Deploy both applications with the updated generated Prisma client. The schema migration must precede the new application code.
4. On the server owning the persistent logo volume, preview optimization using the active backend container:

```sh
docker exec ats_backend_blue node prisma/migrate-logos.cjs
```

After reviewing sizes and errors, apply:

```sh
docker exec ats_backend_blue node prisma/migrate-logos.cjs --apply
```

Use `ats_backend_green` when green is active. The utility processes both inline images and existing tenant-owned file paths, checks HTTP bytes, and updates references only if unchanged since inspection. Each old reference is backed up to a dot-prefixed JSONL file in the logo directory before its database update; dotfiles are denied by the public file server. Failed images are reported and retained unchanged, with a nonzero exit status. Re-running skips already optimized references. Files above the former 2 MB limit require manual review.

Do not apply optimization from a developer computer connected to production: its new image files would exist only locally. Existing file references continue to work, but old files retain their original size until optimized.

## Release gate compatibility

Migration `20261024140000_separate_tenant_logos` carries the required rollback-compatible marker, transaction and five-second local lock timeout. Its one-time copy into the new optional column is approved in the release controller by exact migration identity and SHA-256 of normalized SQL. The original site-logo column is unchanged and previous application images ignore the added field.

Deploy the matching backend migration and orchestrator controller revisions together. Adding only the marker will still fail the data-change review. If the release stopped during validation, this migration was not executed; correct the source and start a new release with the corrected revisions rather than repairing Prisma history or bypassing the guard.

## Header recovery

Branding requests use SWR with three bounded retries and focus/reconnect recovery. Cache keys include user, tenant and workspace identity. Known branding is retained during temporary failures; a saved logo cannot be overwritten by an older response.

Logo images remain visible while their transparent bounds are measured. Cached images are measured even without a new load event. Failed image requests retry twice with a delay and a new request URL, then show accessible company text. Focus or reconnect can restart recovery.

## Verification

- Backend: `npm run build` and `npm test -- --runInBand`.
- Frontend: `node --test tests/branding-recovery.test.cjs tests/sign-in-policy.test.cjs`, `npx tsc --noEmit --incremental false`.
- Contracts: `node scripts/sync-tenant-branding.cjs --check` and `node scripts/sync-sign-in-policy.cjs --check`.
- In a signed-in browser: change/save/reload each logo independently; test removal, each login layout, mobile settings, temporary offline failures and session renewal.

## Rollback

Deploy the previous application version while leaving the additive database column in place. Restore optimized references from the JSONL backup with parameterized, tenant-scoped updates, only where the current value still equals its recorded replacement. Original image files remain available. Back up login-logo values before ever removing the new column.
