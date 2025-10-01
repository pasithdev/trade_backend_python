# 🚀 Deploy Permanent API Credentials Fix - Windows PowerShell Script
# This script deploys the permanent credentials implementation to production

Write-Host "🔒 Deploying Permanent API Credentials Fix to Production" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

$SERVER = "167.71.207.209"
$REMOTE_PATH = "/var/www/trade_backend_python"
$LOCAL_FILE = "src\routes\binance_trading.py"

Write-Host "📁 Target Server: $SERVER" -ForegroundColor Cyan
Write-Host "📁 Remote Path: $REMOTE_PATH" -ForegroundColor Cyan
Write-Host "📁 Local File: $LOCAL_FILE" -ForegroundColor Cyan
Write-Host ""

# Check if local file exists
if (-not (Test-Path $LOCAL_FILE)) {
    Write-Host "❌ Error: Local file $LOCAL_FILE not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Local file found: $LOCAL_FILE" -ForegroundColor Green
Write-Host ""

# Copy updated file to server using SCP
Write-Host "📤 Uploading permanent credentials implementation..." -ForegroundColor Yellow
$remoteFile = "$REMOTE_PATH/$($LOCAL_FILE -replace '\\', '/')"
& scp $LOCAL_FILE "root@${SERVER}:$remoteFile"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ File uploaded successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to upload file!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Restart the Flask application
Write-Host "🔄 Restarting Flask application on production server..." -ForegroundColor Yellow

$sshCommands = @"
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
    echo "📋 Process ID: `$(pgrep -f 'python.*main.py')`"
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
"@

& ssh "root@$SERVER" $sshCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Test webhook endpoints to verify auto-initialization"
    Write-Host "2. Monitor logs for permanent credential usage"
    Write-Host "3. Check webhook success rates for improvement"
    Write-Host ""
    Write-Host "🔗 Test URLs:" -ForegroundColor Cyan
    Write-Host "   State-aware MA Cross: http://$SERVER/api/binance/state-aware-ma-cross-webhook"
    Write-Host "   Super Scalper: http://$SERVER/api/binance/super-scalper-webhook"
    Write-Host "   Target Trend: http://$SERVER/api/binance/target-trend-webhook"
    Write-Host ""
    Write-Host "🧪 Run test script:" -ForegroundColor Yellow
    Write-Host "   python test_permanent_credentials.py"
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above and try again."
    exit 1
}