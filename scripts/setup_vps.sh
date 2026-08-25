#!/usr/bin/env bash
# ==============================================================================
# ATS AWS VPS One-Click Initializer Script
# Run this script once on a fresh AWS EC2 / Lightsail instance (Ubuntu 22.04/24.04)
# Usage:
#   curl -sSL https://raw.githubusercontent.com/enfycon-inc/ATS_DOCKERREPO/main/scripts/setup_vps.sh | bash
# ==============================================================================

set -e

echo "=========================================================="
echo "🚀 Initializing AWS VPS for Enfycon ATS Multi-Tenant Stack"
echo "=========================================================="

# 1. Update system packages
echo "📦 Updating OS packages..."
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y curl wget git unzip htop ca-certificates gnupg lsb-release ufw

# 2. Configure 4GB Swap Space (Prevents OOM during Python / PyTorch / Next.js builds)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 4GB Swap file to prevent build OOM..."
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✓ 4GB Swap allocated successfully."
else
    echo "✓ Swapfile already exists."
fi

# 3. Install Docker Engine and Docker Compose Plugin
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker Engine & Docker Compose Plugin..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Enable non-root docker execution
    sudo usermod -aG docker $USER
    sudo systemctl enable docker
    sudo systemctl start docker
    echo "✓ Docker installed and running."
else
    echo "✓ Docker is already installed."
fi

# 4. Configure UFW Firewall
echo "🛡️ Configuring Firewall (Ports 22, 80, 443)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP Caddy'
sudo ufw allow 443/tcp comment 'HTTPS Caddy'
sudo ufw allow 443/udp comment 'HTTP/3 QUIC'
sudo ufw --force enable
echo "✓ Firewall active."

# 5. Create Deployment Directory
APP_DIR="/var/www/ats"
echo "📁 Setting up project directory at $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

echo "=========================================================="
echo "🎉 AWS VPS Setup Completed Successfully!"
echo "=========================================================="
echo "Next Steps:"
echo "1. Add your AWS VPS Public IP, SSH Username, and Private Key to GitHub Actions Secrets."
echo "2. Point your DNS records (A Record *.enfyjobs.com, enfyjobs.com, api.enfyjobs.com) to this VPS IP."
echo "3. Push to 'main' branch or trigger GitHub Actions to run the first automated deployment."
echo "=========================================================="
