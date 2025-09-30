#!/bin/bash

# Deployment Script for Trade Backend Python on DigitalOcean Droplet
# This script handles the deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===============================================${NC}"
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please run setup_droplet.sh first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running or user is not in docker group."
        print_status "Try: sudo systemctl start docker"
        print_status "Or log out and log back in if you just added user to docker group."
        exit 1
    fi
}

# Check if environment file exists
check_env_file() {
    if [[ ! -f .env.production ]]; then
        print_error "Environment file .env.production not found!"
        print_status "Please create .env.production with required variables:"
        cat << EOF
SECRET_KEY=your-super-secret-key-here
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key
BINANCE_TESTNET=false
REDIS_PASSWORD=your-redis-password
DOMAIN_NAME=yourdomain.com
EMAIL=your-email@domain.com
EOF
        exit 1
    fi
}

# Load environment variables
load_env() {
    print_status "Loading environment variables..."
    set -a  # automatically export all variables
    source .env.production
    set +a
}

# Setup SSL certificates
setup_ssl() {
    if [[ -n "$DOMAIN_NAME" ]]; then
        print_status "Setting up SSL certificates for $DOMAIN_NAME..."
        
        # Check if certificate already exists
        if [[ ! -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]]; then
            print_status "Obtaining SSL certificate..."
            sudo certbot certonly --standalone -d $DOMAIN_NAME --email $EMAIL --agree-tos --no-eff-email
        else
            print_status "SSL certificate already exists for $DOMAIN_NAME"
        fi
        
        # Copy certificates to nginx directory
        sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem nginx/ssl/
        sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem nginx/ssl/
        sudo chown $(whoami):$(whoami) nginx/ssl/*
    else
        print_warning "DOMAIN_NAME not set. Using self-signed certificate for development."
        
        # Generate self-signed certificate
        if [[ ! -f "nginx/ssl/cert.pem" ]]; then
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout nginx/ssl/privkey.pem \
                -out nginx/ssl/fullchain.pem \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        fi
    fi
}

# Build and deploy application
deploy_app() {
    print_header "Building and Deploying Application"
    
    # Pull latest changes
    print_status "Pulling latest code from repository..."
    git pull origin master
    
    # Build and start services
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 30
    
    # Check health
    print_status "Checking application health..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "✅ Application is healthy!"
    else
        print_error "❌ Application health check failed"
        print_status "Checking logs..."
        docker-compose logs --tail=50 web
        exit 1
    fi
}

# Setup automatic SSL renewal
setup_ssl_renewal() {
    if [[ -n "$DOMAIN_NAME" ]]; then
        print_status "Setting up automatic SSL certificate renewal..."
        
        # Create renewal script
        cat > ~/ssl_renew.sh << EOF
#!/bin/bash
certbot renew --quiet
if [[ \$? -eq 0 ]]; then
    cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem ~/trade_backend_python/nginx/ssl/
    cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem ~/trade_backend_python/nginx/ssl/
    cd ~/trade_backend_python
    docker-compose restart nginx
fi
EOF
        
        chmod +x ~/ssl_renew.sh
        
        # Add to crontab
        (crontab -l 2>/dev/null; echo "0 2 * * 0 ~/ssl_renew.sh") | crontab -
        print_status "SSL auto-renewal configured for Sundays at 2 AM"
    fi
}

# Main deployment process
main() {
    print_header "Trade Backend Python - Production Deployment"
    
    # Pre-flight checks
    check_docker
    check_env_file
    load_env
    
    # Setup SSL
    setup_ssl
    
    # Deploy application
    deploy_app
    
    # Setup SSL renewal
    setup_ssl_renewal
    
    print_header "Deployment Completed Successfully! 🎉"
    print_status "Your application is now running at:"
    
    if [[ -n "$DOMAIN_NAME" ]]; then
        echo "  🌐 https://$DOMAIN_NAME"
        echo "  🔍 https://$DOMAIN_NAME/health"
    else
        echo "  🌐 http://$(curl -s ifconfig.me)"
        echo "  🔍 http://$(curl -s ifconfig.me)/health"
    fi
    
    print_status "Useful commands:"
    echo "  📊 View logs: docker-compose logs -f"
    echo "  🔄 Restart: docker-compose restart"
    echo "  📈 Monitor: docker-compose ps"
    echo "  🛑 Stop: docker-compose down"
    echo "  🗑️  Clean: docker-compose down -v && docker system prune -f"
}

# Run main function
main "$@"