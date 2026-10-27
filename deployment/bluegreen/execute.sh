sudo -n --preserve-env=GH_TOKEN,GH_ACTOR,IMAGE_OWNER,OPERATION,RELEASE_ID,ROLLBACK_TARGET,DEPLOY_IMAGES,CONTROLLER_B64 bash -se <<'ATS_RELEASE'
set -euo pipefail
cd /var/www/ats-prod
test -f compose.yml
# Configure ats.slice memory up to 6.5 GB (MemoryMax=6656M, MemoryHigh=6144M)
mkdir -p /etc/systemd/system/ats.slice.d
cat <<'EOF' > /etc/systemd/system/ats.slice.d/override.conf
[Slice]
MemoryHigh=6144M
MemoryMax=6656M
EOF
systemctl daemon-reload 2>/dev/null || true
if systemctl status ats.slice >/dev/null 2>&1; then
  systemctl set-property ats.slice MemoryHigh=6144M MemoryMax=6656M 2>/dev/null || true
fi
if [[ -f /sys/fs/cgroup/ats.slice/memory.max ]]; then
  echo 6979321856 > /sys/fs/cgroup/ats.slice/memory.max 2>/dev/null || true
fi
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
