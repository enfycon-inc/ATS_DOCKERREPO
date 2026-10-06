# ATS GitHub releases

GitHub runs source checks and builds images before the production job can connect
to the VPS. Automatic disposable staging was removed at the user's request to
shorten the pipeline. Production deployments use immutable image digests and a private release
journal at `/var/www/ats-prod/bluegreen/state.json`.

## Use GitHub Actions

Open **ATS CI/CD - blue green production**, choose **Run workflow**, branch `main`.

* `deploy`: check/build the selected service(s), then activate. Normal source
  repository pushes dispatch this automatically. All required jobs must pass.
* `rollback`: leave the target blank for the previous successful release, or enter
  one of the five retained release IDs shown by `status`.
* `status`: display current, previous, retained IDs and any cleanup warning.
* `cleanup`: retry reference-aware cleanup. Never removes database/upload volumes.
* `bootstrap`: convert existing verified application images to release pairs
  without rebuilding them. Downloads the internal proxy during initial setup.
* `existing_release`: optional explicit retry of a previously built `gha-RUN-ATTEMPT`
  image tag. Its digest is resolved on the runner; production readiness checks
  still run before traffic switches.

## What happens on the VPS

1. Acquire the same exclusive lock used by local deployment tools.
2. Capture the initial infrastructure, secrets and mounted adapter configuration
   privately. Refuse changed Prisma schemas pending a compatible migration review.
3. Check memory/disk headroom inside the existing ATS allocation. Start a new
   frontend/backend pair; each frontend addresses its own backend.
4. Check running image identities, readiness, password login and refresh. Preserve
   retained Next.js static assets for browsers opened before the release.
5. Back up the database/uploads. Wait for both targets in the internal HAProxy to
   become healthy, then change one runtime map entry for frontend/API/TLS-domain
   authorization together. Caddy continues running with unchanged routes. Verify
   public routes and observe candidate health before recording success.
6. Keep the active and immediate previous HTTP pair warm. Retain five successful
   complete release manifests/images; drain/remove older containers and prune only
   owned, unreferenced application images/assets. Shared image layers are deduplicated.

The immediate previous warm HTTP release switches without a build/pull/restart.
Existing requests and upgraded connections keep their original upstream; new
requests use the selected release. HAProxy uses 64 MiB inside the existing ATS
allocation and exposes no host ports. Its administration socket is root-only.
The one-time conversion to the stable proxy requires a Caddy reload; routine
deployments and rollbacks do not reload either proxy. Persistent map/server files
and the release journal allow recovery after a process/VPS restart.
Older retained versions need startup and health checks. Parser changes need memory
for another parser; Celery worker changes wait for active tasks to finish. Queued
tasks remain in Redis. Worker handoffs and older-version recovery are not instant.

Build/test failure skips the production job entirely. Activation failure restores
the verified previous routing. An interrupted deployment/rollback keeps a durable
pending record for recovery on the next operation or VPS reboot.

`ats-release-cleanup.timer` retries cleanup every 15 minutes. Draining requests/jobs
can temporarily defer deletion; a warning is visible in `status`. `backup.sh` uses
the active release rather than a retired Compose container. Application services
are removed from the infrastructure Compose declaration after conversion, while
PostgreSQL, Redis, Keycloak and Caddy continue running. Avoid the older local
dashboard deployment path after conversion; use these GitHub operations.
Adding another application's routes to Caddy requires reviewing the controller's
base configuration too. External routing changes stop deployment for review
instead of being overwritten by an older ATS routing snapshot.

## Prerequisites and limits

Repository secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, optional `VPS_PORT`,
and `GH_PAT` for the private source checkouts. The verified host-key fingerprint
is stored in the repository variable `VPS_HOST_FINGERPRINT`.

No automatic schema synchronization or destructive migrations are permitted.
Use backward-compatible migrations that work with active and rollback images.
Backups are retained locally for seven days; this does not replace off-server
backup storage. The allocation remains one CPU / 3,800 MiB and can refuse a rollout
under load. One VPS is not high availability against host/database outages.

Full backend tests are intentionally enforced. Existing application test failures
must be resolved rather than bypassed to publish a new backend build. The initial
bootstrap reuses the already-running application binaries.

## Faster verification alternative

Normal releases keep source checks, parallel cached builds, candidate health,
password login/refresh checks, and automatic recovery on failed activation.
They do not create temporary accounts or jobs. Run the retained isolated
`stage.py` / `stage-smoke.cjs` checks manually when authentication, account,
job, permission, or database behavior changes. These checks need a disposable
environment and must never be pointed at the production database. A permanent
team staging site and shared development environment remain unconfigured.
