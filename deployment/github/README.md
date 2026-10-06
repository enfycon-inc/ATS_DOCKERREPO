# GitHub Actions production deployment

The existing root workflow builds Docker images on GitHub runners, publishes
run-specific tags to GHCR, then uses SSH to deploy to `/var/www/ats-prod`.
Microservice repository dispatches deploy only the originating service; parser
deployments restart its worker too. Root pushes and normal manual runs deploy all.

Root repository Actions secrets: `VPS_HOST`, `VPS_SSH_KEY`, `VPS_USER` (default
`ubuntu`), `VPS_PORT` (default `22`), and `GH_PAT` for the private source repositories.
The SSH user must have passwordless sudo, matching the current VPS installation.
Each microservice repository needs its existing `GH_PAT` dispatch secret and an
enabled trigger workflow. Credentials are managed in GitHub; none belong in Git.

Manual runs can select one service. To retry only deployment, supply the existing
`gha-RUN-ATTEMPT` image tag in `existing_release`; GitHub skips the build jobs and
deploys those images through the same schema, backup and health checks.

Use **Run workflow → check_only** to test the actual GitHub SSH secrets without
building or deploying. Leave it unchecked for normal deployment. Builds must
succeed before the deployment job starts.

Deployment preserves the existing compose file, environment, database volumes,
TLS configuration and resource limits. It takes a backup, changes only application
image settings, checks health, and restores previous application images on failure.
Previous environment snapshots stay under `github-releases/` with mode 600.
It never runs schema migrations or removes old images. Backend schema differences
stop deployment for separate migration review; CRLF/LF line endings are normalized.
Backup and health commands cannot consume the script's standard input. Success
requires matching the running container image IDs to the selected release; an
early end of input is treated as failure. The existing parser runtime mounts
remain active. Application restarts can briefly interrupt requests.
