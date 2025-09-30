#!/bin/bash

# DigitalOcean Droplet Setup Script for Trade Backend Python
# Run this script on a fresh Ubuntu 22.04 Droplet

set -e

echo "🚀 Starting DigitalOcean Droplet setup for Trade Backend Python..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   print_status "Please run as a regular user with sudo privileges"
   exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
print_status "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $(whoami)
rm get-docker.sh

# Install Docker Compose
print_status "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install essential tools
print_status "Installing essential tools..."
sudo apt install -y git curl wget htop nano vim ufw fail2ban certbot python3-certbot-nginx

# Setup firewall
print_status "Configuring UFW firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Configure fail2ban
print_status "Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create application directory
print_status "Creating application directory..."
mkdir -p ~/trade_backend_python
cd ~/trade_backend_python

# Create necessary directories
mkdir -p logs nginx/ssl backups src/database

# Set proper permissions
sudo chown -R $(whoami):$(whoami) ~/trade_backend_python

print_status "✅ Basic server setup completed!"
print_warning "⚠️  Please log out and log back in for Docker group changes to take effect"
print_status "Next steps:"
echo "1. Clone your repository: git clone https://github.com/pasithdev/trade_backend_python.git"
echo "2. Copy .env.production file and configure environment variables"
echo "3. Run: ./deploy/deploy.sh"
echo ""
print_status "🔐 Security recommendations:"
echo "- Change SSH port from default 22"
echo "- Setup SSH key authentication and disable password auth"
echo "- Configure regular security updates"
echo "- Setup monitoring and alerting"