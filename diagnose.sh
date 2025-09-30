#!/bin/bash

# DigitalOcean troubleshooting script for App Platform connectivity issues

echo "=== DigitalOcean App Platform Network Diagnostics ==="
echo "App URL: https://whale-app-864sn.ondigitalocean.app/"
echo "Generated: $(date)"
echo ""

echo "1. Testing internal health check..."
curl -s -o /dev/null -w "Health check status: %{http_code}, Response time: %{time_total}s\n" http://localhost:8080/health 2>/dev/null || echo "❌ Health check failed (container not accessible)"

echo ""
echo "2. Testing root endpoint..."
curl -s -o /dev/null -w "Root endpoint status: %{http_code}, Response time: %{time_total}s\n" http://localhost:8080/ 2>/dev/null || echo "❌ Root endpoint failed"

echo ""
echo "3. Current server configuration..."
echo "PORT: ${PORT:-8080}"
echo "ENVIRONMENT: ${ENVIRONMENT:-development}"
echo "PYTHONPATH: ${PYTHONPATH:-/workspace}"

echo ""
echo "4. Process information..."
ps aux | grep -E "(gunicorn|python)" || echo "❌ No Python/Gunicorn processes found"

echo ""
echo "5. Network binding check..."
netstat -tlnp 2>/dev/null | grep ":${PORT:-8080}" || echo "❌ Port ${PORT:-8080} not bound"

echo ""
echo "=== Troubleshooting Steps ==="
echo "If health checks pass but external access fails:"
echo "1. Check DigitalOcean App Platform dashboard for SSL certificate status"
echo "2. Verify domain routing is active in the Components > web section"
echo "3. Try disabling HTTP/3 (QUIC) in networking settings"
echo "4. Redeploy the app to refresh edge routing"
echo "5. Contact DigitalOcean support if connection resets persist"