#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ATS ZERO-DOWNTIME BLUE/GREEN DEPLOYMENT ENGINE
# ─────────────────────────────────────────────────────────────────────────────
# Manages seamless, zero-downtime deployments by building & starting
# the idle container stack (Blue or Green), verifying HTTP health checks,
# reloading Caddy atomically (0 ms cutover), and gracefully stopping the old stack.
# ─────────────────────────────────────────────────────────────────────────────
set -e
export GIT_TERMINAL_PROMPT=0
export DOCKER_BUILDKIT=1
export COMPOSE_PARALLEL_LIMIT=4

APP_DIR="/var/www/ats"
cd "$APP_DIR"

dc() {
  env -i PATH="$PATH" HOME="$HOME" USER="$USER" docker compose "$@"
}

echo "=========================================================="
echo "🚀 Starting ATS Zero-Downtime Blue/Green Deployment Engine"
echo "=========================================================="

# 1. Determine current active slot (Blue or Green)
ACTIVE_COLOR="blue"
if [ -f "$APP_DIR/.active_color" ]; then
  ACTIVE_COLOR=$(cat "$APP_DIR/.active_color")
elif [ -f "$APP_DIR/caddy_upstreams/backend.caddy" ]; then
  if grep -q "backend_green" "$APP_DIR/caddy_upstreams/backend.caddy"; then
    ACTIVE_COLOR="green"
  fi
fi

if [ "$ACTIVE_COLOR" = "blue" ]; then
  TARGET_COLOR="green"
else
  TARGET_COLOR="blue"
fi

echo "🟢 Current Active Slot:  [${ACTIVE_COLOR^^}]"
echo "🎯 Deploying Target Slot: [${TARGET_COLOR^^}]"

# 2. Ensure caddy_upstreams directory exists
mkdir -p "$APP_DIR/caddy_upstreams"

# 3. Pull / Sync Microservice repositories
echo "📦 Syncing Microservice codebases..."
if [ -d "ats_frontend_main/.git" ]; then
  ( cd ats_frontend_main && git remote set-url origin git@github.com:enfycon-inc/ats_frontend_main.git && git fetch origin main && git reset --hard origin/main )
else
  git clone git@github.com:enfycon-inc/ats_frontend_main.git ats_frontend_main
fi

if [ -d "ats_backend/.git" ]; then
  ( cd ats_backend && git remote set-url origin git@github.com:enfycon-inc/ats_backend.git && git fetch origin main && git reset --hard origin/main )
else
  git clone git@github.com:enfycon-inc/ats_backend.git ats_backend
fi

if [ -d "resume-parser-main/.git" ]; then
  ( cd resume-parser-main && git remote set-url origin git@github.com:enfycon-inc/resume-parser.git && git fetch origin main && git reset --hard origin/main )
else
  git clone git@github.com:enfycon-inc/resume-parser.git resume-parser-main
fi

# 4. Ensure shared infrastructure is up (Redis, Resume Parser, Celery, Keycloak, Caddy)
echo "⚡ Ensuring shared core infrastructure is running..."
dc -f docker-compose.prod.yml up -d --no-recreate redis api worker keycloak caddy

# 5. Build Target Slot Docker images
echo "🐳 Building Target [${TARGET_COLOR^^}] Docker containers in parallel..."
dc -f docker-compose.prod.yml build --parallel "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}"

# 6. Launch Target Slot containers
echo "🚀 Starting Target [${TARGET_COLOR^^}] containers..."
dc -f docker-compose.prod.yml up -d "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}"

# 7. Health Check Verification Gate
echo "🩺 Verifying health of Target [${TARGET_COLOR^^}] containers before traffic cutover..."
BACKEND_HEALTHY=0
FRONTEND_HEALTHY=0
MAX_RETRIES=30
RETRY_INTERVAL=2

for ((i=1; i<=MAX_RETRIES; i++)); do
  echo "🔍 [Attempt $i/$MAX_RETRIES] Checking container readiness..."
  
  if [ $BACKEND_HEALTHY -eq 0 ]; then
    if docker exec "ats_backend_${TARGET_COLOR}" wget -qO- http://localhost:5000/api/health >/dev/null 2>&1; then
      echo "  ✅ ats_backend_${TARGET_COLOR} is HEALTHY!"
      BACKEND_HEALTHY=1
    fi
  fi

  if [ $FRONTEND_HEALTHY -eq 0 ]; then
    if docker exec "ats_frontend_${TARGET_COLOR}" wget -qO- http://localhost:3000/api/health >/dev/null 2>&1; then
      echo "  ✅ ats_frontend_${TARGET_COLOR} is HEALTHY!"
      FRONTEND_HEALTHY=1
    fi
  fi

  if [ $BACKEND_HEALTHY -eq 1 ] && [ $FRONTEND_HEALTHY -eq 1 ]; then
    echo "🎉 All Target [${TARGET_COLOR^^}] services passed health checks and are fully operational!"
    break
  fi

  sleep $RETRY_INTERVAL
done

if [ $BACKEND_HEALTHY -eq 0 ] || [ $FRONTEND_HEALTHY -eq 0 ]; then
  echo "❌ Health check FAILED for Target [${TARGET_COLOR^^}] stack within timeout!"
  echo "📋 Target Backend Logs:"
  docker logs "ats_backend_${TARGET_COLOR}" --tail 30 || true
  echo "📋 Target Frontend Logs:"
  docker logs "ats_frontend_${TARGET_COLOR}" --tail 30 || true
  echo "🛑 Aborting deployment. Stopping unhealthy target containers..."
  dc -f docker-compose.prod.yml stop "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}" || true
  echo "🔒 Active [${ACTIVE_COLOR^^}] stack remains 100% online and untouched. ZERO downtime."
  exit 1
fi

# 8. Seamless Traffic Cutover via Caddy Atomic Reload
echo "🔄 Performing 0-ms atomic traffic switch in Caddy to [${TARGET_COLOR^^}]..."

cat <<EOF > "$APP_DIR/caddy_upstreams/backend.caddy"
reverse_proxy backend_${TARGET_COLOR}:5000 {
    lb_try_duration 3s
    lb_try_interval 250ms
}
EOF

cat <<EOF > "$APP_DIR/caddy_upstreams/frontend.caddy"
reverse_proxy frontend_${TARGET_COLOR}:3000 {
    lb_try_duration 3s
    lb_try_interval 250ms
}
EOF

cat <<EOF > "$APP_DIR/caddy_upstreams/ask.caddy"
ask http://backend_${TARGET_COLOR}:5000/api/auth/check-ssl-domain
EOF

# Reload Caddy in-memory
docker exec ats_caddy caddy reload --config /etc/caddy/Caddyfile

# Record new active color
echo "$TARGET_COLOR" > "$APP_DIR/.active_color"
echo "✨ Traffic successfully routed to [${TARGET_COLOR^^}] stack!"

# 9. Graceful Connection Draining & Old Stack Shutdown
echo "⏳ Waiting 5s for in-flight requests on [${ACTIVE_COLOR^^}] to complete..."
sleep 5

echo "🛑 Gracefully stopping previous [${ACTIVE_COLOR^^}] stack..."
dc -f docker-compose.prod.yml stop "backend_${ACTIVE_COLOR}" "frontend_${ACTIVE_COLOR}" || true

# 10. Clean up dangling images
echo "🧹 Cleaning up dangling build images..."
docker image prune -f || true

# 11. Final Live Smoke Test
echo "🌐 Running public endpoint verification:"
curl -sk -I https://enfyjobs.com/api/health --max-time 8 | grep -E 'HTTP|Server|Location' || echo "Frontend check warning"
curl -sk -I https://api.enfyjobs.com/api/health --max-time 8 | grep -E 'HTTP|Server|Location' || echo "Backend check warning"

echo "=========================================================="
echo "✅ Zero-Downtime Deployment to [${TARGET_COLOR^^}] Complete!"
echo "=========================================================="
