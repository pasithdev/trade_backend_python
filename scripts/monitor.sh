#!/bin/bash

# System Monitoring Script for Trade Backend Python
# Monitors system health, application status, and sends alerts

set -e

# Configuration
APP_DIR="/home/$(whoami)/trade_backend_python"
LOG_FILE="$APP_DIR/logs/monitor.log"
ALERT_EMAIL="${EMAIL:-admin@localhost}"
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=85

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[MONITOR]${NC} $1"
    echo "$(date): $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date): WARNING - $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date): ERROR - $1" >> "$LOG_FILE"
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    if command -v mail &> /dev/null && [[ "$ALERT_EMAIL" != "admin@localhost" ]]; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
    fi
    
    print_error "ALERT: $subject - $message"
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

print_status "Starting system monitoring..."

# Check system resources
check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    local cpu_int=${cpu_usage%.*}
    
    if [[ $cpu_int -gt $CPU_THRESHOLD ]]; then
        send_alert "High CPU Usage" "CPU usage is at ${cpu_usage}% (threshold: ${CPU_THRESHOLD}%)"
        return 1
    fi
    
    print_status "CPU usage: ${cpu_usage}%"
    return 0
}

check_memory() {
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [[ $mem_usage -gt $MEMORY_THRESHOLD ]]; then
        send_alert "High Memory Usage" "Memory usage is at ${mem_usage}% (threshold: ${MEMORY_THRESHOLD}%)"
        return 1
    fi
    
    print_status "Memory usage: ${mem_usage}%"
    return 0
}

check_disk() {
    local disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    
    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        send_alert "High Disk Usage" "Disk usage is at ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
        return 1
    fi
    
    print_status "Disk usage: ${disk_usage}%"
    return 0
}

# Check Docker containers
check_containers() {
    cd "$APP_DIR"
    
    local unhealthy_containers=$(docker-compose ps | grep -v "Up" | grep -v "Name" | wc -l)
    
    if [[ $unhealthy_containers -gt 0 ]]; then
        local container_status=$(docker-compose ps)
        send_alert "Container Health Issue" "$unhealthy_containers containers are not running properly:\n$container_status"
        return 1
    fi
    
    print_status "All containers are healthy"
    return 0
}

# Check application health
check_app_health() {
    local health_url="http://localhost:8000/health"
    
    if ! curl -f -s "$health_url" > /dev/null; then
        send_alert "Application Health Check Failed" "Health endpoint $health_url is not responding"
        return 1
    fi
    
    print_status "Application health check passed"
    return 0
}

# Check SSL certificate expiration
check_ssl_cert() {
    if [[ -n "$DOMAIN_NAME" ]] && [[ -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]]; then
        local cert_expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" | cut -d= -f2)
        local cert_expiry_epoch=$(date -d "$cert_expiry" +%s)
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( ($cert_expiry_epoch - $current_epoch) / 86400 ))
        
        if [[ $days_until_expiry -lt 30 ]]; then
            send_alert "SSL Certificate Expiring" "SSL certificate for $DOMAIN_NAME expires in $days_until_expiry days"
            return 1
        fi
        
        print_status "SSL certificate expires in $days_until_expiry days"
    fi
    return 0
}

# Check log file sizes
check_log_sizes() {
    local max_log_size=100M  # 100MB
    
    find "$APP_DIR/logs" -name "*.log" -size +$max_log_size 2>/dev/null | while read -r logfile; do
        local size=$(du -h "$logfile" | cut -f1)
        print_warning "Large log file detected: $logfile ($size)"
    done
}

# Main monitoring function
main() {
    local errors=0
    
    check_cpu || ((errors++))
    check_memory || ((errors++))
    check_disk || ((errors++))
    check_containers || ((errors++))
    check_app_health || ((errors++))
    check_ssl_cert || ((errors++))
    check_log_sizes
    
    if [[ $errors -eq 0 ]]; then
        print_status "All systems operational ✅"
    else
        print_error "$errors issues detected ❌"
    fi
    
    return $errors
}

# Run monitoring
main "$@"