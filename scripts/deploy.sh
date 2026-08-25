#!/usr/bin/env bash
# ==============================================================================
# Manual / On-Server Deploy Script for Enfycon ATS Stack
# Usage:
#   bash scripts/deploy.sh
# ==============================================================================

set -e

echo "🚀 Starting Production Stack Deployment..."

# 1. Update git submodules / repos if in git
if [ -d ".git" ]; then
    echo "🔄 Pulling latest orchestrator changes..."
    git pull origin main
fi

# 2. Build and launch containers
echo "🐳 Launching production containers with Caddy SSL..."
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# 3. Clean old images
echo "🧹 Pruning dangling docker build cache..."
docker image prune -f

# 4. Status
echo "📊 Current Container Status:"
docker compose -f docker-compose.prod.yml ps

echo "✅ Production Stack is Live!"
