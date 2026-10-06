sudo -n --preserve-env=GH_TOKEN,GH_ACTOR,IMAGE_OWNER,OPERATION,RELEASE_ID,ROLLBACK_TARGET,DEPLOY_IMAGES,CONTROLLER_B64 bash -se <<'ATS_RELEASE'
set -euo pipefail
cd /var/www/ats-prod
test -f compose.yml
mkdir -p bluegreen
chmod 700 bluegreen
printf '%s' "$CONTROLLER_B64" | base64 -d > "bluegreen/controller-${RELEASE_ID}.py"
chmod 700 "bluegreen/controller-${RELEASE_ID}.py"
docker_config=$(mktemp -d)
trap 'rm -rf "$docker_config"' EXIT
export DOCKER_CONFIG="$docker_config"
if [[ "$OPERATION" == deploy && "$DEPLOY_IMAGES" != '{}' ]]; then
  printf '%s' "$GH_TOKEN" | docker login ghcr.io -u "$GH_ACTOR" --password-stdin
fi
unset GH_TOKEN CONTROLLER_B64
# Controller reports success only after verifying the live image IDs and routes.
# Preserve its stable entry point for nightly backups and reboot reconciliation.
install -m 700 "bluegreen/controller-${RELEASE_ID}.py" bluegreen/release.py.next
mv -f bluegreen/release.py.next bluegreen/release.py
python3 bluegreen/release.py /var/www/ats-prod "$OPERATION" </dev/null
ATS_RELEASE
