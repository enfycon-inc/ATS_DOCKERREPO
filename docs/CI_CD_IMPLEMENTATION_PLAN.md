# System Design Proposal: GitHub CI/CD with blue/green deployment

## Objectives and current architecture

GitHub Actions builds and publishes frontend, backend and parser images to GHCR.
Production currently runs one container per service and deploys by restarting it.
Caddy serves the root, API, authentication and dynamic tenant domains. The ATS
resource allocation is one CPU and 3,800 MiB RAM. The measured cgroup usage during
planning was approximately 2.1 GiB; this is an idle observation, not a load guarantee.

Target: uninterrupted frontend/API releases, immediate rollback to the previous
healthy release, at most five successful release snapshots retained on the VPS,
and no production image pulls or changes when CI builds/tests fail.

## Release and CI model

1. Resolve immutable source revisions for every affected repository. Run lint,
   type checks, meaningful tests and image builds on GitHub runners. Integration
   tests use disposable runner databases/Redis, never production data.
2. Publish images with unique identifiers and resolve their registry digests.
   All required build/test jobs must pass before any VPS deployment job begins.
3. Create a complete application release manifest: image digests/source revisions
   for frontend, backend, parser/worker, runtime adapter/config versions, and
   database compatibility requirements. Unchanged services carry forward their
   current versions. A partial build success is not a successful release.
4. Serialize production deployments and rollbacks using GitHub concurrency and a
   VPS lock. Reject stale releases and insufficient disk/memory headroom.
5. Preserve explicit build, deploy, verify, rollback and cleanup results in GitHub
   summaries and the VPS release journal. Cleanup failure must be visible without
   falsely marking an otherwise healthy deployment as rolled back.

## Blue/green frontend and backend

Create release-specific frontend/backend container pairs on the existing private
network. Each frontend calls its own backend. Both use the existing secrets,
database, Redis and shared uploads, with identical tenant/auth settings.

Normally keep the current and immediate previous successful pair running. While
preparing another deployment, use a temporary candidate pair so preparation does
not remove the current rollback target. Check capacity before starting it; abort
instead of raising the ATS allocation or risking the live application's memory.
At current container limits, one additional pair reserves up to 576 MiB. Two
additional pairs reserve up to 1,152 MiB. Load tests must establish adequate margin.

Validate candidate image identity, dependency readiness, login/session refresh,
tenant isolation, permissions, job/account creation and existing API contracts.
Prevent duplicate scheduled jobs and unsafe startup side effects when multiple
backends run together. Preserve old Next.js assets and test browser deployment
version skew rather than relying on the homepage health check alone.

Implementation refinement: availability checks found brief connection resets
while reloading Caddy. Keep Caddy's root, tenant, API and certificate-authorization
routes fixed through an internal HAProxy. Switch one runtime map entry after both
release targets are healthy, without reloading either proxy. Keep previous
upstreams available for in-flight requests and upgraded connections. Persist
validated server addresses and the selected map for restarts; reconcile an
interrupted operation to the last successful journal entry. The proxy reserves
64 MiB within the existing ATS allocation and exposes only a root-only Unix
administration socket, with no public administration port. The one-time proxy
conversion requires a Caddy reload and is distinct from routine releases.

The initial conversion keeps today's live containers serving traffic while the
first candidate starts and is checked. It must not require compose down or remove
the existing volumes.

## Verification and rollback

After switching, verify public routes and the expected running image digests, then
observe a defined health window before recording the release as successful.
If checks fail, select the previous runtime routing map, verify recovery and
record the failed candidate. Keep a durable journal so interrupted SSH/GitHub
runs can reconcile the actual Caddy configuration and container versions.

Provide a manual GitHub rollback action accepting a retained release ID. The
immediate previous warm frontend/backend pair can receive traffic in seconds
without building, downloading or restarting it. Older retained releases start
and pass checks while the active release continues serving; this takes startup
time. Keeping all five releases warm is not included in the 50% resource budget.
Rollback does not restore database data or undo destructive migrations.

## Parser, worker and infrastructure

Use the same CI gates, immutable manifests and retention rules for parser/worker.
Roll out the parser API behind an internal switching route only when sufficient
memory exists for an additional ready parser. Drain in-flight requests before
retiring the old process. Version the mounted parser adapters with the release;
an image rollback alone must not silently retain incompatible adapter code.

Workers stop consuming new tasks, complete active tasks and are replaced with
compatible workers. Redis holds queued work during the handoff. Verify task
acknowledgement/retry settings and idempotency. Do not promise instant worker
rollback or uninterrupted task execution solely from blue/green HTTP routing.
If capacity is inadequate, stop the deployment and preserve the working release.

PostgreSQL, Redis, Keycloak and Caddy are shared infrastructure. Their upgrades
require a separate maintenance/availability design. A single VPS remains a single
point of failure; this plan covers application releases, not machine failure.

## Retain five successful releases

Count the active successful release plus four prior successful release snapshots.
Failed candidates do not enter this list. After a verified deployment, protect
every image/config referenced by these five snapshots and by any live candidate,
active or rollback container. Remove retired stopped application containers and
then only ATS images/config artifacts unreferenced by that protected set.

Never use broad Docker image/volume pruning. Never delete database/upload/TLS
volumes or images belonging to other projects. Shared image layers mean five
snapshots do not necessarily mean five images per repository. Clean failed
candidate artifacts after recovery and remove superseded transfer files. Keep
database backups under their separate retention policy. If rollback activates an
older retained release, it remains protected until it leaves the retained set.

## Database, security and performance

- Use compatible additive migrations; destructive changes require a later
  reviewed release after incompatible rollback versions have been retired.
- Back up before reviewed production schema changes; never run automatic schema
  reset/db push. Verify contracts against both current and previous application
  versions. Mark incompatible historical releases unavailable for rollback.
- Retain private networks and current RBAC/tenant ownership checks. Store secrets
  in GitHub/VPS secret configuration, never in public release manifests.
- Pin SSH server identity and restrict registry/deployment credentials. Do not
  expose candidate ports or Caddy's administration endpoint publicly.
- Enforce capacity checks within the existing ATS slice; do not change the reserve
  for the future EnfySync project. Release infrastructure adds no application API
  round trips or database queries to normal user requests.

## Implementation and acceptance sequence

1. Add release manifests/journal, CI gates and regression tests without changing
   live routing. Test build failure leaves the VPS unchanged.
2. Add candidate pairs and Caddy switching; convert the current installation while
   keeping its live containers available.
3. Add previous-release warm standby, manual/automatic rollback and digest checks.
4. Add reference-aware five-release cleanup and storage reporting.
5. Integrate parser/worker rollout and versioned adapters with resource admission.
6. Rehearse bad health, wrong images, genuine schema changes, CRLF differences,
   interrupted SSH, invalid Caddy configuration, failed cleanup and task draining.
7. Under representative traffic, verify no dropped normal HTTP requests during
   release/rollback, preserved sessions and tenant routing, no duplicate jobs,
   safe restart recovery, and no deletion of retained rollback artifacts.

Production activation follows these acceptance checks. No deployment code or VPS
configuration has been changed by preparing this proposal.
