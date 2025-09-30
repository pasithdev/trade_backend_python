#!/bin/bash

# Automated Backup Script for Trade Backend Python
# Backs up database, logs, and configuration files

set -e

# Configuration
BACKUP_DIR="/home/$(whoami)/backups"
APP_DIR="/home/$(whoami)/trade_backend_python"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[BACKUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_status "Starting backup process..."

# Backup database
if [[ -f "$APP_DIR/src/database/app.db" ]]; then
    print_status "Backing up SQLite database..."
    cp "$APP_DIR/src/database/app.db" "$BACKUP_DIR/database_$DATE.db"
    gzip "$BACKUP_DIR/database_$DATE.db"
fi

# Backup configuration files
print_status "Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C "$APP_DIR" \
    docker-compose.yml \
    .env.production \
    nginx/nginx.conf \
    gunicorn.conf.py \
    2>/dev/null || true

# Backup logs
if [[ -d "$APP_DIR/logs" ]]; then
    print_status "Backing up logs..."
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$APP_DIR" logs/
fi

# Create application state snapshot
print_status "Creating application state snapshot..."
cat > "$BACKUP_DIR/state_$DATE.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "docker_images": $(docker images --format 'json' | jq -s '.'),
    "running_containers": $(docker ps --format 'json' | jq -s '.'),
    "disk_usage": "$(df -h /)",
    "memory_usage": "$(free -h)",
    "system_uptime": "$(uptime)"
}
EOF

# Cleanup old backups
print_status "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

# Create backup summary
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)

print_status "Backup completed successfully!"
echo "  📁 Backup directory: $BACKUP_DIR"
echo "  📊 Total size: $BACKUP_SIZE"
echo "  📈 Files count: $BACKUP_COUNT"
echo "  🕒 Retention: $RETENTION_DAYS days"

# Send notification if email is configured
if command -v mail &> /dev/null && [[ -n "$EMAIL" ]]; then
    echo "Backup completed successfully on $(hostname) at $(date)" | \
        mail -s "Trade Backend Backup Success" "$EMAIL"
fi