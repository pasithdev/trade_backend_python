# DigitalOcean Droplet Production Deployment Guide

## 🚀 Complete Guide to Deploy Trade Backend Python on DigitalOcean Droplet

This guide will help you deploy your Trade Backend Python application on a DigitalOcean Droplet with production-ready configuration including SSL, monitoring, backups, and automated management.

---

## 📋 Prerequisites

### 1. DigitalOcean Account & Droplet
- Create a DigitalOcean account at [digitalocean.com](https://digitalocean.com)
- Create a new Droplet:
  - **OS**: Ubuntu 22.04 LTS
  - **Size**: Basic droplet, 2GB RAM minimum (4GB recommended)
  - **Region**: Choose closest to your users
  - **Authentication**: SSH keys (recommended) or password
  - **Hostname**: `trade-backend-prod` or similar

### 2. Domain Name (Recommended)
- Purchase a domain name or subdomain
- Point A record to your Droplet's IP address
- Example: `api.yourdomain.com -> YOUR_DROPLET_IP`

### 3. Required Accounts
- **Binance API**: Get API keys from [Binance API Management](https://www.binance.com/en/my/settings/api-management)
- **Email Service**: Gmail or other SMTP provider for notifications

---

## 🛠️ Step 1: Initial Droplet Setup

### Connect to Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
# or
ssh -i ~/.ssh/your_key root@YOUR_DROPLET_IP
```

### Create Non-Root User (Security Best Practice)
```bash
# Create user
adduser trader
usermod -aG sudo trader

# Copy SSH keys (if using key authentication)
rsync --archive --chown=trader:trader ~/.ssh /home/trader
```

### Switch to New User
```bash
su - trader
```

### Run Initial Setup Script
```bash
# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/pasithdev/trade_backend_python/master/deploy/setup_droplet.sh -o setup_droplet.sh
chmod +x setup_droplet.sh
./setup_droplet.sh
```

**Important**: Log out and log back in after setup to activate Docker group membership:
```bash
exit
ssh trader@YOUR_DROPLET_IP
```

---

## 📦 Step 2: Deploy Application

### Clone Repository
```bash
cd ~
git clone https://github.com/pasithdev/trade_backend_python.git
cd trade_backend_python
```

### Configure Environment Variables
```bash
# Copy environment template
cp .env.production.template .env.production

# Edit with your values
nano .env.production
```

**Required Environment Variables:**
```bash
# Application Settings
SECRET_KEY=generate-a-super-secure-random-key-here
ENVIRONMENT=production

# Binance API
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key
BINANCE_TESTNET=false

# Domain & SSL
DOMAIN_NAME=api.yourdomain.com
EMAIL=your-email@domain.com

# Security
REDIS_PASSWORD=your-secure-redis-password
```

### Run Deployment
```bash
# Make deployment script executable
chmod +x deploy/deploy.sh

# Deploy application
./deploy/deploy.sh
```

The deployment script will:
- ✅ Obtain SSL certificate from Let's Encrypt
- ✅ Build Docker containers
- ✅ Start all services (web, nginx, redis)
- ✅ Configure automatic SSL renewal
- ✅ Verify application health

---

## 🔧 Step 3: Verify Deployment

### Check Application Status
```bash
# View running containers
docker-compose ps

# Check application health
curl https://api.yourdomain.com/health

# View logs
docker-compose logs -f web
```

### Test Your Endpoints
```bash
# Main application
curl https://api.yourdomain.com/

# API status
curl https://api.yourdomain.com/api/status

# Test TradingView webhook (example)
curl -X POST https://api.yourdomain.com/api/tradingview/webhook \
  -H "Content-Type: application/json" \
  -d '{"action": "test", "symbol": "BTCUSDT"}'
```

---

## 🛡️ Step 4: Security Hardening

### Configure Firewall Rules
```bash
# Basic firewall setup (already done by setup script)
sudo ufw status

# Additional rules if needed
sudo ufw allow from YOUR_HOME_IP to any port 22  # Restrict SSH
sudo ufw delete allow 22  # Remove open SSH rule
```

### Setup SSH Key Authentication (if not done)
```bash
# Disable password authentication
sudo nano /etc/ssh/sshd_config

# Set these values:
# PasswordAuthentication no
# PermitRootLogin no

sudo systemctl restart ssh
```

### Setup Automatic Security Updates
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📊 Step 5: Monitoring & Management

### Daily Management Commands
```bash
# Make management script executable
chmod +x scripts/manage.sh

# Check application status
./scripts/manage.sh status

# View logs
./scripts/manage.sh logs web

# Restart services
./scripts/manage.sh restart

# Update application
./scripts/manage.sh update

# Create backup
./scripts/manage.sh backup

# Monitor system health
./scripts/manage.sh monitor
```

### Setup Automated Monitoring
```bash
# Add monitoring to crontab
crontab -e

# Add these lines:
# Check health every 5 minutes
*/5 * * * * /home/trader/trade_backend_python/scripts/monitor.sh >> /home/trader/trade_backend_python/logs/cron.log 2>&1

# Daily backup at 2 AM
0 2 * * * /home/trader/trade_backend_python/scripts/backup.sh >> /home/trader/trade_backend_python/logs/backup.log 2>&1

# Weekly log cleanup
0 3 * * 0 find /home/trader/trade_backend_python/logs -name "*.log" -mtime +7 -delete
```

---

## 🔄 Step 6: Ongoing Maintenance

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update application
./scripts/manage.sh update

# Clean up Docker resources
./scripts/manage.sh clean
```

### Backup Management
```bash
# Manual backup
./scripts/manage.sh backup

# View backups
ls -la ~/backups/

# Restore database (example)
cd ~/trade_backend_python
docker-compose exec web python -c "
import os
os.system('cp /app/backups/database_YYYYMMDD_HHMMSS.db.gz /tmp/')
os.system('gunzip /tmp/database_YYYYMMDD_HHMMSS.db.gz')
os.system('cp /tmp/database_YYYYMMDD_HHMMSS.db /app/src/database/app.db')
"
docker-compose restart web
```

### SSL Certificate Management
```bash
# Check certificate status
sudo certbot certificates

# Manual renewal (automatic renewal is configured)
./scripts/manage.sh ssl-renew

# Test automatic renewal
sudo certbot renew --dry-run
```

---

## 🚨 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
./scripts/manage.sh logs web

# Common fixes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal

# Update nginx
cp /etc/letsencrypt/live/DOMAIN/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/DOMAIN/privkey.pem nginx/ssl/
docker-compose restart nginx
```

#### High Resource Usage
```bash
# Check system resources
./scripts/manage.sh monitor

# View container resources
docker stats

# Restart heavy containers
docker-compose restart web
```

#### Database Issues
```bash
# Check database file
ls -la src/database/

# Backup current database
cp src/database/app.db src/database/app.db.backup

# Reset database (WARNING: destroys data)
rm src/database/app.db
docker-compose restart web
```

### Log Locations
- **Application logs**: `~/trade_backend_python/logs/`
- **Nginx logs**: `~/trade_backend_python/logs/nginx/`
- **System logs**: `/var/log/`
- **Docker logs**: `docker-compose logs [service]`

---

## 📞 Support & Maintenance

### Health Check URLs
- **Application**: `https://yourdomain.com/health`
- **API Status**: `https://yourdomain.com/api/status`

### Important Files
- **Environment**: `.env.production`
- **Docker Compose**: `docker-compose.yml`
- **Nginx Config**: `nginx/nginx.conf`
- **SSL Certificates**: `nginx/ssl/`

### Performance Optimization
- **Scale containers**: Increase `instance_count` in docker-compose.yml
- **Upgrade Droplet**: Resize Droplet in DigitalOcean dashboard
- **Enable Redis caching**: Already configured in docker-compose.yml
- **Database optimization**: Consider PostgreSQL for high traffic

---

## 🎉 Congratulations!

Your Trade Backend Python application is now running in production on DigitalOcean Droplet with:

- ✅ **HTTPS/SSL encryption** with automatic renewal
- ✅ **Reverse proxy** with Nginx for performance and security
- ✅ **Containerized deployment** with Docker Compose
- ✅ **Automated backups** and monitoring
- ✅ **Security hardening** with firewall and fail2ban
- ✅ **Management scripts** for easy maintenance
- ✅ **High availability** configuration

Your trading bot is ready to receive TradingView webhooks and execute trades securely! 🚀

---

## 📚 Additional Resources

- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)