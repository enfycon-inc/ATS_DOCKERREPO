sudo -n --preserve-env=GH_TOKEN,GH_ACTOR,IMAGE_OWNER,RELEASE_TAG,DISPATCH_REPO,EVENT_NAME,SERVICE bash -se <<'ATS_DEPLOY'
set -euo pipefail
deployment_complete=false
cleanup() {
  local code=$?
  trap - EXIT
  if [[ -n "${DOCKER_CONFIG:-}" ]]; then rm -rf "$DOCKER_CONFIG"; fi
  if [[ "$code" == 0 && "$deployment_complete" != true ]]; then
    echo 'Deployment ended before running-image verification completed' >&2
    code=1
  fi
  exit "$code"
}
trap cleanup EXIT
cd /var/www/ats-prod
test -f compose.yml
test -f .env
test -f backup.sh
exec 9>.dashboard.lock
flock -n 9 || { echo 'Another production deployment is running'; exit 1; }
case "${EVENT_NAME}" in
  repository_dispatch)
    case "${DISPATCH_REPO}" in
      enfycon-inc/ats_frontend_main) services=(frontend);;
      enfycon-inc/ats_backend) services=(backend);;
      enfycon-inc/resume-parser) services=(parser);;
      *) echo 'Unknown service repository'; exit 1;;
    esac;;
  workflow_dispatch)
    case "${SERVICE:-all}" in
      all) services=(frontend backend parser);;
      frontend|backend|parser) services=("$SERVICE");;
      *) echo 'Unknown selected service'; exit 1;;
    esac;;
  *) services=(frontend backend parser);;
esac
[[ "$RELEASE_TAG" =~ ^gha-[0-9]+-[0-9]+$ ]]
[[ "$IMAGE_OWNER" =~ ^[a-zA-Z0-9_-]+$ ]]
# Keep registry credentials temporary; production secrets remain on the VPS.
export DOCKER_CONFIG
DOCKER_CONFIG=$(mktemp -d)
printf '%s' "$GH_TOKEN" | docker login ghcr.io -u "$GH_ACTOR" --password-stdin
unset GH_TOKEN
for service in "${services[@]}"; do
  remote="ghcr.io/${IMAGE_OWNER,,}/ats-${service}:${RELEASE_TAG}"
  docker pull "$remote"
  docker tag "$remote" "ats-${service}:prod-${RELEASE_TAG}"
done
# Do not apply unreviewed database changes automatically.
if [[ " ${services[*]} " == *' backend '* ]]; then
  container=$(docker compose -f compose.yml ps -q backend)
  test -n "$container"
  # Ignore CRLF/LF differences only; keep real schema changes blocked.
  old_schema=$(docker exec "$container" cat /app/prisma/schema.prisma </dev/null | sed 's/\r$//')
  new_schema=$(docker run --rm --entrypoint cat "ats-backend:prod-${RELEASE_TAG}" /app/prisma/schema.prisma </dev/null | sed 's/\r$//')
  [[ -n "$old_schema" && -n "$new_schema" ]] || { echo 'Cannot read Prisma schema'; exit 1; }
  [[ "$old_schema" == "$new_schema" ]] || { echo 'Prisma schema changed: apply a reviewed migration separately'; exit 1; }
fi
# The script itself arrives on stdin. Backup commands must not consume it.
sh ./backup.sh </dev/null
mkdir -p github-releases
previous="github-releases/${RELEASE_TAG}.env"
cp .env "$previous"
chmod 600 "$previous"
targets=("${services[@]}")
[[ " ${services[*]} " != *' parser '* ]] || targets+=(worker)
wait_healthy() {
  local attempt service container state health
  for attempt in {1..45}; do
    local ready=true
    for service in "${targets[@]}"; do
      container=$(docker compose -f compose.yml ps -q "$service")
      if [[ -z "$container" ]]; then ready=false; continue; fi
      state=$(docker inspect -f '{{.State.Status}}' "$container")
      health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container")
      [[ "$state" == running && "$health" != starting && "$health" != unhealthy ]] || ready=false
      if [[ "$service" == parser ]]; then
        docker compose -f compose.yml exec -T --interactive=false parser python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=4).read()" </dev/null >/dev/null 2>&1 || ready=false
      fi
    done
    if $ready; then return 0; fi
    sleep 4
  done
  return 1
}
restore() {
  trap - ERR
  echo 'Deployment failed; restoring previous application images'
  cp "$previous" .env
  docker compose -f compose.yml up -d --no-deps "${targets[@]}"
  wait_healthy || echo 'Rollback health checks failed: review VPS logs'
  exit 1
}
trap restore ERR
python3 - "$RELEASE_TAG" "${services[@]}" <<'PY'
from pathlib import Path
import re, sys
path = Path('.env')
text = path.read_text()
for service in sys.argv[2:]:
    key = service.upper() + '_IMAGE'
    text, count = re.subn(r'^' + key + r'=.*$', key + '=ats-' + service + ':prod-' + sys.argv[1], text, flags=re.M)
    if count != 1:
        raise ValueError('Missing or duplicate image setting: ' + key)
temp = Path('.env.github-tmp')
temp.write_text(text)
temp.chmod(0o600)
temp.replace(path)
PY
docker compose -f compose.yml config --quiet
docker compose -f compose.yml up -d --no-deps "${targets[@]}"
wait_healthy
sleep 10
wait_healthy
for service in "${targets[@]}"; do
  image_service="$service"
  [[ "$service" != worker ]] || image_service=parser
  expected=$(docker image inspect -f '{{.Id}}' "ats-${image_service}:prod-${RELEASE_TAG}")
  container=$(docker compose -f compose.yml ps -q "$service")
  actual=$(docker inspect -f '{{.Image}}' "$container")
  [[ "$actual" == "$expected" ]] || { echo "Running image mismatch: $service"; false; }
  echo "Verified running image: $service / $expected"
done
printf '%s\n' "$RELEASE_TAG" > github-releases/current
deployment_complete=true
trap - ERR
echo "Deployment successful: ${RELEASE_TAG} / ${services[*]}"
ATS_DEPLOY
