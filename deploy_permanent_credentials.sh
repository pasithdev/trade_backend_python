#!/bin/bash

# 🚀 Deploy Permanent API Credentials Fix
# This script deploys the permanent credentials implementation to production

echo "🔒 Deploying Permanent API Credentials Fix to Production"
echo "========================================================"

SERVER="167.71.207.209"
REMOTE_PATH="/var/www/trade_backend_python"
LOCAL_FILE="src/routes/binance_trading.py"

echo "📁 Target Server: $SERVER"
echo "📁 Remote Path: $REMOTE_PATH"
echo "📁 Local File: $LOCAL_FILE"
echo ""

# Check if local file exists
if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ Error: Local file $LOCAL_FILE not found!"
    exit 1
fi

echo "✅ Local file found: $LOCAL_FILE"
echo ""

# Copy updated file to server
echo "📤 Uploading permanent credentials implementation..."
scp "$LOCAL_FILE" "root@$SERVER:$REMOTE_PATH/$LOCAL_FILE"

if [ $? -eq 0 ]; then
    echo "✅ File uploaded successfully!"
else
    echo "❌ Failed to upload file!"
    exit 1
fi

echo ""

# Restart the Flask application
echo "🔄 Restarting Flask application on production server..."
ssh root@$SERVER << 'EOF'
    cd /var/www/trade_backend_python
    
    # Stop existing processes
    echo "⏹️ Stopping existing Flask processes..."
    pkill -f "python.*main.py" || true
    pkill -f "gunicorn" || true
    
    # Wait a moment
    sleep 2
    
    # Start the application
    echo "🚀 Starting Flask application with permanent credentials..."
    nohup python3 src/main.py > trading_system.log 2>&1 &
    
    # Check if process started
    sleep 3
    if pgrep -f "python.*main.py" > /dev/null; then
        echo "✅ Flask application started successfully!"
        echo "📋 Process ID: $(pgrep -f 'python.*main.py')"
    else
        echo "❌ Failed to start Flask application!"
        echo "📋 Checking logs..."
        tail -n 20 trading_system.log
        exit 1
    fi
    
    # Show initialization status
    echo ""
    echo "🔍 Checking auto-initialization logs..."
    tail -n 10 trading_system.log | grep -i "auto-initializ\|binance client\|permanent"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Next Steps:"
    echo "1. Test webhook endpoints to verify auto-initialization"
    echo "2. Monitor logs for permanent credential usage"
    echo "3. Check webhook success rates for improvement"
    echo ""
    echo "🔗 Test URLs:"
    echo "   State-aware MA Cross: http://$SERVER/api/binance/state-aware-ma-cross-webhook"
    echo "   Super Scalper: http://$SERVER/api/binance/super-scalper-webhook"
    echo "   Target Trend: http://$SERVER/api/binance/target-trend-webhook"
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the error messages above and try again."
    exit 1
fi