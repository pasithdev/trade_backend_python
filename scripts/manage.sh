#!/bin/bash

# Management Script for Trade Backend Python
# Provides easy commands for common operations

set -e

# Configuration
APP_DIR="/home/$(whoami)/trade_backend_python"
SCRIPT_DIR="$APP_DIR/scripts"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# Change to app directory
cd "$APP_DIR"

# Commands
cmd_status() {
    print_header "Application Status"
    docker-compose ps
    echo ""
    print_status "System Resources:"
    echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')%"
    echo "  Memory: $(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')%"
    echo "  Disk: $(df / | awk 'NR==2{print $5}')%"
}

cmd_logs() {
    local service="${1:-web}"
    print_header "Viewing Logs for $service"
    docker-compose logs -f --tail=100 "$service"
}

cmd_restart() {
    local service="${1:-all}"
    if [[ "$service" == "all" ]]; then
        print_header "Restarting All Services"
        docker-compose restart
    else
        print_header "Restarting $service"
        docker-compose restart "$service"
    fi
}

cmd_update() {
    print_header "Updating Application"
    
    # Pull latest code
    print_status "Pulling latest code..."
    git pull origin master
    
    # Rebuild and restart
    print_status "Rebuilding containers..."
    docker-compose build --no-cache
    
    print_status "Restarting services..."
    docker-compose up -d
    
    # Wait for health check
    print_status "Waiting for health check..."
    sleep 30
    
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "✅ Update completed successfully!"
    else
        print_error "❌ Health check failed after update"
        cmd_logs web
    fi
}

cmd_backup() {
    print_header "Creating Backup"
    if [[ -f "$SCRIPT_DIR/backup.sh" ]]; then
        bash "$SCRIPT_DIR/backup.sh"
    else
        print_error "Backup script not found at $SCRIPT_DIR/backup.sh"
    fi
}

cmd_monitor() {
    print_header "System Monitoring"
    if [[ -f "$SCRIPT_DIR/monitor.sh" ]]; then
        bash "$SCRIPT_DIR/monitor.sh"
    else
        print_error "Monitor script not found at $SCRIPT_DIR/monitor.sh"
    fi
}

cmd_shell() {
    local service="${1:-web}"
    print_header "Opening Shell in $service Container"
    docker-compose exec "$service" /bin/bash
}

cmd_clean() {
    print_header "Cleaning Up Docker Resources"
    print_warning "This will remove unused containers, networks, and images"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down
        docker system prune -f
        docker volume prune -f
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

cmd_ssl_renew() {
    print_header "Renewing SSL Certificate"
    if [[ -n "$DOMAIN_NAME" ]]; then
        sudo certbot renew
        # Copy renewed certificates
        sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem nginx/ssl/
        sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem nginx/ssl/
        sudo chown $(whoami):$(whoami) nginx/ssl/*
        docker-compose restart nginx
        print_status "SSL certificate renewed and nginx restarted"
    else
        print_error "DOMAIN_NAME not configured"
    fi
}

cmd_help() {
    print_header "Trade Backend Python - Management Commands"
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status              Show application and system status"
    echo "  logs [service]      View logs (default: web)"
    echo "  restart [service]   Restart service (default: all)"
    echo "  update              Pull latest code and rebuild"
    echo "  backup              Create backup of database and configs"
    echo "  monitor             Run system health monitoring"
    echo "  shell [service]     Open shell in container (default: web)"
    echo "  clean               Clean up Docker resources"
    echo "  ssl-renew           Renew SSL certificate"
    echo "  help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 logs web"
    echo "  $0 restart nginx"
    echo "  $0 shell web"
}

# Main command handler
case "${1:-help}" in
    "status")
        cmd_status
        ;;
    "logs")
        cmd_logs "$2"
        ;;
    "restart")
        cmd_restart "$2"
        ;;
    "update")
        cmd_update
        ;;
    "backup")
        cmd_backup
        ;;
    "monitor")
        cmd_monitor
        ;;
    "shell")
        cmd_shell "$2"
        ;;
    "clean")
        cmd_clean
        ;;
    "ssl-renew")
        cmd_ssl_renew
        ;;
    "help"|*)
        cmd_help
        ;;
esac