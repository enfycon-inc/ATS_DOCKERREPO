#!/bin/bash
set -e

APP_DIR="/var/www/ats"
cd "$APP_DIR"

# 1. Determine Blue/Green Target
if [ ! -f .active_color ]; then
  ACTIVE_COLOR="none"
  TARGET_COLOR="blue"
else
  ACTIVE_COLOR=$(cat .active_color)
  if [ "$ACTIVE_COLOR" == "blue" ]; then
    TARGET_COLOR="green"
  else
    TARGET_COLOR="blue"
  fi
fi

echo "?? Active Slot: [${ACTIVE_COLOR^^}] | ?? Target Slot: [${TARGET_COLOR^^}]"

# 2. Ensure shared infrastructure is up
echo "??? Ensuring shared core infrastructure is running..."
PG_STATUS=$(docker inspect -f '{{.State.Status}}' ats_postgres 2>/dev/null || true)
PG_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' ats_postgres 2>/dev/null || true)
if [ "$PG_STATUS" = "exited" ] || [ "$PG_HEALTH" = "unhealthy" ]; then
  echo "?? Detected unhealthy/exited ats_postgres container, removing for clean initialization..."
  docker rm -f ats_postgres 2>/dev/null || true
fi

KC_STATUS=$(docker inspect -f '{{.State.Status}}' ats_keycloak 2>/dev/null || true)
if [ "$KC_STATUS" = "restarting" ] || [ "$KC_STATUS" = "exited" ]; then
  echo "?? Detected unhealthy/restarting ats_keycloak container, removing for clean start..."
  docker rm -f ats_keycloak 2>/dev/null || true
fi


echo "?? Cleaning up old Docker build cache and unused images to free up VPS disk space..."
echo "?? VPS Disk Space BEFORE Cleanup:"
df -h /

docker builder prune -af || true
docker image prune -af || true

echo "?? VPS Disk Space AFTER Cleanup:"
df -h /

# Pull core images
docker compose -f docker-compose.prod.yml pull postgres redis keycloak pgadmin caddy
docker compose -f docker-compose.prod.yml up -d postgres redis api worker keycloak pgadmin caddy

# Ensure PostgreSQL is ready
echo "? Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if docker exec ats_postgres pg_isready -U ats_user -d ats_db >/dev/null 2>&1; then
    echo "? PostgreSQL is ready."
    break
  fi
  sleep 1
done

docker exec ats_postgres psql -U ats_user -d ats_db -c "ALTER DATABASE ats_db SET search_path = ats, mass_mail, public; ALTER USER ats_user SET search_path = ats, mass_mail, public;" || true
docker exec -i ats_postgres psql -U ats_user -d ats_db < scripts/init-schemas.sql || true

ACTUAL_USERS=$(docker exec ats_postgres psql -U ats_user -d ats_db -tAc "SELECT count(*) FROM ats.users;" 2>/dev/null || echo "0")
if [ "$ACTUAL_USERS" = "0" ]; then
  echo "?? Initializing production database with seed data..."
  docker exec -i ats_postgres psql -U ats_user -d ats_db < scripts/production_seed_data.sql || true
fi

# Ensure Keycloak is ready
echo "? Waiting for Keycloak to be ready on port 8080..."
for i in {1..35}; do
  if curl -sf http://127.0.0.1:8080/realms/enfycon-ats >/dev/null 2>&1; then
    echo "? Keycloak is ready."
    break
  fi
  sleep 2
done

# 3. Pull Pre-built Target Slot Docker images
echo "?? Pulling pre-built Target [${TARGET_COLOR^^}] Docker containers from GHCR..."
docker compose -f docker-compose.prod.yml pull "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}"

# 4. Launch Target Slot containers
echo "?? Starting Target [${TARGET_COLOR^^}] containers..."
docker compose -f docker-compose.prod.yml rm -f -s -v "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}" || true
docker rm -f "ats_backend_${TARGET_COLOR}" "ats_frontend_${TARGET_COLOR}" || true
docker compose -f docker-compose.prod.yml up -d --force-recreate "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}"

# 5. Health Check Verification Gate
echo "?? Verifying health of Target [${TARGET_COLOR^^}] containers..."
BACKEND_HEALTHY=0
FRONTEND_HEALTHY=0
MAX_RETRIES=60
RETRY_INTERVAL=2

for ((i=1; i<=MAX_RETRIES; i++)); do
  if [ $BACKEND_HEALTHY -eq 0 ]; then
    if docker exec "ats_backend_${TARGET_COLOR}" node -e "require('http').get('http://127.0.0.1:5000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))" >/dev/null 2>&1; then
      BACKEND_HEALTHY=1
    fi
  fi
  if [ $FRONTEND_HEALTHY -eq 0 ]; then
    if docker exec "ats_frontend_${TARGET_COLOR}" node -e "require('http').get('http://127.0.0.1:3000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))" >/dev/null 2>&1; then
      FRONTEND_HEALTHY=1
    fi
  fi
  if [ $BACKEND_HEALTHY -eq 1 ] && [ $FRONTEND_HEALTHY -eq 1 ]; then
    echo "? All Target [${TARGET_COLOR^^}] services are healthy!"
    break
  fi
  sleep $RETRY_INTERVAL
done

if [ $BACKEND_HEALTHY -eq 0 ] || [ $FRONTEND_HEALTHY -eq 0 ]; then
  echo "? Health check FAILED for Target [${TARGET_COLOR^^}]!"
  
  echo "========== BACKEND LOGS =========="
  docker logs "ats_backend_${TARGET_COLOR}" --tail 100
  echo "========== FRONTEND LOGS =========="
  docker logs "ats_frontend_${TARGET_COLOR}" --tail 100
  
  docker compose -f docker-compose.prod.yml stop "backend_${TARGET_COLOR}" "frontend_${TARGET_COLOR}" || true
  exit 1
fi

# 6. Seamless Traffic Cutover via Caddy
echo "?? Performing traffic switch in Caddy to [${TARGET_COLOR^^}]..."

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

docker exec ats_caddy caddy reload --config /etc/caddy/Caddyfile || true

echo "$TARGET_COLOR" > "$APP_DIR/.active_color"
echo "? Traffic successfully routed to [${TARGET_COLOR^^}] stack!"

# 7. Graceful Shutdown of Old Stack
if [ "$ACTIVE_COLOR" != "none" ]; then
  sleep 5
  docker compose -f docker-compose.prod.yml stop "backend_${ACTIVE_COLOR}" "frontend_${ACTIVE_COLOR}" || true
fi

# Clean up dangling images
docker image prune -f || true

echo "?? Zero-Downtime Deployment to [${TARGET_COLOR^^}] Complete!"
