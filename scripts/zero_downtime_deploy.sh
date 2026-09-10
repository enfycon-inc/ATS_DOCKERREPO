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
  env -i PATH="$PATH" HOME="$HOME" USER="$USER" POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-AtsDevPass2024}" docker compose "$@"
}

echo "=========================================================="
echo "🚀 Starting ATS Zero-Downtime Blue/Green Deployment Engine"
echo "=========================================================="

# 1. Determine active container slot by inspecting live running containers
BLUE_RUNNING=$(docker ps -q --filter "name=ats_backend_blue" --filter "status=running" 2>/dev/null || true)
GREEN_RUNNING=$(docker ps -q --filter "name=ats_backend_green" --filter "status=running" 2>/dev/null || true)

if [ -n "$GREEN_RUNNING" ] && [ -z "$BLUE_RUNNING" ]; then
  ACTIVE_COLOR="green"
  TARGET_COLOR="blue"
elif [ -n "$BLUE_RUNNING" ]; then
  ACTIVE_COLOR="blue"
  TARGET_COLOR="green"
else
  # Initial Bootstrap: deploy blue slot
  ACTIVE_COLOR="none"
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

# 4. Ensure shared infrastructure is up (Postgres, Redis, Resume Parser, Celery, Keycloak, Caddy)
echo "⚡ Ensuring shared core infrastructure is running..."
PG_STATUS=$(docker inspect -f '{{.State.Status}}' ats_postgres 2>/dev/null || true)
PG_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' ats_postgres 2>/dev/null || true)
if [ "$PG_STATUS" = "exited" ] || [ "$PG_HEALTH" = "unhealthy" ]; then
  echo "⚠️ Detected unhealthy/exited ats_postgres container, removing for clean initialization..."
  docker rm -f ats_postgres 2>/dev/null || true
fi

KC_STATUS=$(docker inspect -f '{{.State.Status}}' ats_keycloak 2>/dev/null || true)
if [ "$KC_STATUS" = "restarting" ] || [ "$KC_STATUS" = "exited" ]; then
  echo "⚠️ Detected unhealthy/restarting ats_keycloak container, removing for clean start..."
  docker rm -f ats_keycloak 2>/dev/null || true
fi

dc -f docker-compose.prod.yml up -d postgres redis api worker keycloak pgadmin caddy

# Ensure PostgreSQL is accepting connections and schemas are initialized
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if docker exec ats_postgres pg_isready -U ats_user -d ats_db >/dev/null 2>&1; then
    echo "✅ PostgreSQL is ready."
    break
  fi
  sleep 1
done

# Ensure search_path is set permanently on both database and user
docker exec ats_postgres psql -U ats_user -d ats_db -c "ALTER DATABASE ats_db SET search_path = ats, mass_mail, public; ALTER USER ats_user SET search_path = ats, mass_mail, public;" || true
docker exec -i ats_postgres psql -U ats_user -d ats_db < scripts/init-schemas.sql || true

# Seed database if users table is empty
ACTUAL_USERS=$(docker exec ats_postgres psql -U ats_user -d ats_db -tAc "SELECT count(*) FROM ats.users;" 2>/dev/null || echo "0")
if [ "$ACTUAL_USERS" = "0" ]; then
  echo "📦 Database has 0 users. Initializing production database with seed data..."
  docker exec -i ats_postgres psql -U ats_user -d ats_db < scripts/production_seed_data.sql || true
fi

# Ensure Keycloak is accepting connections before building/starting backend
echo "⏳ Waiting for Keycloak to be ready on port 8080..."
for i in {1..35}; do
  if curl -sf http://127.0.0.1:8080/realms/enfycon-ats >/dev/null 2>&1; then
    echo "✅ Keycloak is ready and enfycon-ats realm is responsive."
    break
  fi
  sleep 2
done

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
MAX_RETRIES=60
RETRY_INTERVAL=2

for ((i=1; i<=MAX_RETRIES; i++)); do
  echo "🔍 [Attempt $i/$MAX_RETRIES] Checking container readiness..."
  
  if [ $BACKEND_HEALTHY -eq 0 ]; then
    if docker exec "ats_backend_${TARGET_COLOR}" node -e "require('http').get('http://localhost:5000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))" >/dev/null 2>&1; then
      echo "  ✅ ats_backend_${TARGET_COLOR} is HEALTHY!"
      BACKEND_HEALTHY=1
    fi
  fi

  if [ $FRONTEND_HEALTHY -eq 0 ]; then
    if docker exec "ats_frontend_${TARGET_COLOR}" node -e "require('http').get('http://localhost:3000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))" >/dev/null 2>&1; then
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
  docker logs "ats_backend_${TARGET_COLOR}" --tail 40 || true
  echo "📋 Target Frontend Logs:"
  docker logs "ats_frontend_${TARGET_COLOR}" --tail 40 || true
  echo "🛑 Aborting deployment. Stopping unhealthy target containers..."
  dc -f docker-compose.prod.yml stop "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}" || true
  if [ "$ACTIVE_COLOR" != "none" ]; then
    echo "🔒 Active [${ACTIVE_COLOR^^}] stack remains 100% online and untouched. ZERO downtime."
  fi
  exit 1
fi

# 8. Seamless Traffic Cutover via Caddy Atomic Reload
echo "🔄 Performing 0-ms atomic traffic switch in Caddy to [${TARGET_COLOR^^}]..."

if [ "$ACTIVE_COLOR" != "none" ]; then
  cat <<EOF > "$APP_DIR/caddy_upstreams/backend.caddy"
reverse_proxy backend_${TARGET_COLOR}:5000 backend_${ACTIVE_COLOR}:5000 {
    lb_policy first
    lb_try_duration 4s
    lb_try_interval 200ms
    fail_duration 5s
}
EOF

  cat <<EOF > "$APP_DIR/caddy_upstreams/frontend.caddy"
reverse_proxy frontend_${TARGET_COLOR}:3000 frontend_${ACTIVE_COLOR}:3000 {
    lb_policy first
    lb_try_duration 4s
    lb_try_interval 200ms
    fail_duration 5s
}
EOF
else
  cat <<EOF > "$APP_DIR/caddy_upstreams/backend.caddy"
reverse_proxy backend_${TARGET_COLOR}:5000 {
    lb_try_duration 4s
    lb_try_interval 200ms
}
EOF

  cat <<EOF > "$APP_DIR/caddy_upstreams/frontend.caddy"
reverse_proxy frontend_${TARGET_COLOR}:3000 {
    lb_try_duration 4s
    lb_try_interval 200ms
}
EOF
fi

cat <<EOF > "$APP_DIR/caddy_upstreams/ask.caddy"
ask http://backend_${TARGET_COLOR}:5000/api/auth/check-ssl-domain
EOF

# Reload Caddy in-memory
docker exec ats_caddy caddy reload --config /etc/caddy/Caddyfile || true

# Record new active color
echo "$TARGET_COLOR" > "$APP_DIR/.active_color"
echo "✨ Traffic successfully routed to [${TARGET_COLOR^^}] stack!"

# 9. Graceful Connection Draining & Old Stack Shutdown
if [ "$ACTIVE_COLOR" != "none" ]; then
  echo "⏳ Waiting 5s for in-flight requests on [${ACTIVE_COLOR^^}] to complete..."
  sleep 5

  echo "🛑 Gracefully stopping previous [${ACTIVE_COLOR^^}] stack..."
  dc -f docker-compose.prod.yml stop "backend_${ACTIVE_COLOR}" "frontend_${ACTIVE_COLOR}" || true
fi

# Clean up legacy single-instance containers if they lingered
docker stop ats_backend ats_frontend 2>/dev/null || true
docker rm ats_backend ats_frontend 2>/dev/null || true

# 10. Clean up dangling images
echo "🧹 Cleaning up dangling build images..."
docker image prune -f || true

# 11. Final Live Smoke Test
echo "🌐 Running public endpoint verification:"
sleep 2
curl -sk -I https://enfyjobs.com/api/health --max-time 8 | grep -E 'HTTP|Server|Location' || echo "Frontend check warning"
curl -sk -I https://api.enfyjobs.com/api/health --max-time 8 | grep -E 'HTTP|Server|Location' || echo "Backend check warning"

echo "=========================================================="
echo "✅ Zero-Downtime Deployment to [${TARGET_COLOR^^}] Complete!"
echo "=========================================================="
