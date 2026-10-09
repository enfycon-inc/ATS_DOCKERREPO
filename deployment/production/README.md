# ATS production on 13.238.201.190

The VPS has 2 CPUs and 7.6 GiB RAM. ATS containers run under `ats.slice`:
CPU quota 100% (one CPU), memory high 3400 MiB, hard maximum 3800 MiB,
and no swap. Per-container limits total 3776 MiB. These limits reserve
roughly half the CPU/RAM for future EnfySync. They do not reserve disk I/O
or network bandwidth. The operating system and Docker also need headroom.

Production directory: `/var/www/ats-prod`. Compose project: `ats-prod`.
PostgreSQL publishes 5432 on IPv4/IPv6 following explicit owner authorization on
7 October 2026. Public connections to ats_db as ats_user require TLS and SCRAM
password authentication; the internal Docker subnet retains application access.
Use db.enfyjobs.com with SSL enabled in pgAdmin. Redis has no public port mapping.
The VPS uses the trusted Caddy certificate for db.enfyjobs.com; renew-db-tls.sh
and /etc/cron.d/ats-db-tls synchronize renewed certificates every 15 minutes.
Caddy owns 80/443.
Future EnfySync must have separate project/volume/network names and proxy
routes. Never replace this PostgreSQL volume with EnfySync's database.

## Release

Application images are built locally for linux/amd64 from archived Git
commits. Never build on this VPS. The October 5 reference releases are
frontend a641d72 and backend 9a2f23c. Newer frontend HEAD failed type checking
and is not included. The parser uses a CPU-only deployment Dockerfile and
bundled models. A tracked read-only parser-database.py adapter isolates
legacy parser candidates from ATS candidates and maps shared resume IDs
to the Prisma UUID type. Both parser services must mount this adapter. The tracked parser-runtime.py also removes a function-local re import that caused job-description parsing to fail; both services mount this correction. Its resolved dependency versions are recorded in parser-requirements.lock;
retain the image digest for reproduction.

Export images with Docker save, compress, upload through SSH, compare
SHA-256 checksums, and load them. Change image variables in `.env` only
after the exact images pass checks. `docker compose -f compose.yml up -d`
replaces services without recreating persistent volumes. Never run `down -v`.
Keep previous image tags for rollback; restore old image variables and run
`up -d` for the affected application services. A database restore is not an
ordinary application rollback and can lose newer writes.

## Database

Fresh provisioning uses the backend image's checked-in Prisma migrations through
the one-shot `migrate` Compose service. Backend/parser/worker startup waits for it
to finish. It requires a backend image containing `0_production_baseline`; older
images without migration history are not suitable for a new database. The old
`baseline.sql` and `compatibility.sql` files are historical artifacts and are no
longer mounted into PostgreSQL initialization. The Prisma baseline includes shared
parser tables and compatibility operators. Dictionary/admin provisioning remains
an explicit separate step after schema migration.
Existing databases must be verified/backed up and baselined with Prisma resolve;
do not replay baseline SQL or run db push/reset. The current VPS was adopted on
7 October 2026 without recreating tables. AuthInitService still contains
legacy startup DDL/role seeding; removing it is separate application work.
Run `smoke.cjs` inside the backend to exercise fresh tenant registration,
approval, login, refresh, branches, units, schedule persistence, job creation
and isolation. It creates a disposable verification workspace and stores
its identifiers in `/tmp/ats-smoke-identifiers.json` for scoped cleanup.

## Secrets and integrations

New credentials are generated on the VPS in mode-600 `.env` and
`.env.backend`. OAuth/SMTP integrations are intentionally unconfigured per
user instruction. Password authentication is enabled. Email delivery and
external SSO require separate configuration and verification.

## Backups

`backup.sh` makes nightly database and upload backups with seven-day local
retention. Local backups do not survive total VPS/disk loss. Off-server
backup destination, encryption-key custody and alerts must still be
configured. Periodically restore into a separate database and verify data.

## Development and staging

Do not point development or staging to this production database or realm.
Use a separate non-production PostgreSQL instance and unique database,
Keycloak realm, secrets, uploads, and domain names for each environment.
Do not continuously run those extra stacks within the reserved EnfySync
capacity. Staging promotion needs frontend API configuration isolated from
production: the current frontend embeds NEXT_PUBLIC_API_URL at build time.
Until runtime configuration is implemented, build staging separately with
its own API URL and never claim it is the identical production image.

DNS must be changed by the owner to this VPS only after internal checks
pass: enfyjobs.com, api.enfyjobs.com, auth.enfyjobs.com and *.enfyjobs.com.
Caddy certificate issuance and public browser authentication are verified
after DNS propagation. Tenant certificate requests are gated by the
backend check-ssl-domain endpoint.

## Verified deployment — October 6, 2026

DNS for root/API/auth and enfy tenant resolves to 13.238.201.190. Trusted HTTPS checks passed for all four hosts. Password sign-in through the public HTTPS frontend created a valid authenticated session. Internal checks passed registration, approval, tenant login, refresh, permissions/isolation, branch/unit creation, schedule persistence, job creation, resume processing with UUID persistence and cleanup, and job-description parsing. Nightly backup creation and an isolated database restore were tested. These smoke checks are not a guarantee that every product workflow is error-free. Development and staging stacks are not deployed by this production setup.

## Contact route compatibility update

Backend release prod-9a2f23c-contacts-v1 adds /api/clients/:clientId/contacts as an alias for the existing /clients/:clientId/contacts controller. Its base is the same October 5 image, plus the locally compiled controller described in contact-route-alias.patch. No schema or dependencies change. Docker Desktop failed locally during its WSL runtime startup; package-contact-image.py creates a Docker-loadable image from the verified saved base archive and locally compiled controller. The controller source and both HTTP routes have regression tests. The next normal Docker build should include the alias in source. Rollback restores BACKEND_IMAGE from .env.before-contact-alias and recreates only backend.

Production verification passed contact creation/retrieval through both aliases over trusted public HTTPS, creator database identity, unauthenticated rejection and cross-tenant service isolation. All verification clients, contacts and the temporary tenant were removed. Two preflight verification-script mistakes triggered rollback before the final passing deployment; no customer records were changed.
