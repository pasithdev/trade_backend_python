#!/bin/bash
# EMERGENCY SERVER FIX SCRIPT
# Run this on your server: 167.71.207.209

echo "🚨 EMERGENCY SERVER DIAGNOSTIC & FIX 🚨"
echo "Server: 167.71.207.209"
echo "Time: $(date)"

# 1. Kill all existing Python processes to prevent conflicts
echo "1. Stopping all Python processes..."
pkill -f main.py
pkill -f python
sleep 3

# 2. Check for remaining processes
echo "2. Checking for remaining processes..."
ps aux | grep python

# 3. Clear any corrupted temporary files
echo "3. Clearing temporary files..."
rm -f *.pyc
rm -rf __pycache__
rm -f *.log.lock

# 4. Check disk space
echo "4. Checking disk space..."
df -h

# 5. Check memory
echo "5. Checking memory..."
free -h

# 6. Start application fresh
echo "6. Starting application..."
cd /path/to/your/app  # UPDATE THIS PATH!
nohup python src/main.py > trading_system.log 2>&1 &
echo "Application started with PID: $!"

# 7. Wait for startup
echo "7. Waiting for application startup..."
sleep 5

# 8. Test basic connectivity
echo "8. Testing basic connectivity..."
curl -s http://localhost/ || echo "❌ Server not responding"

# 9. Configure API credentials (CRITICAL FIX)
echo "9. Configuring Binance API credentials..."
curl -X POST http://localhost/api/binance/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ",
    "api_secret": "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF",
    "testnet": false
  }'

# 10. Verify API configuration
echo -e "\n10. Verifying API configuration..."
curl -s http://localhost/api/binance/status

# 11. Test webhook with larger position size
echo -e "\n11. Testing webhook with optimized position size..."
curl -X POST http://localhost/api/binance/state-aware-ma-cross-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETHUSDT",
    "action": "buy", 
    "balance_percentage": 0.50,
    "leverage": 10,
    "entry": 2456.78
  }'

echo -e "\n✅ Emergency fix complete!"
echo "Monitor the logs: tail -f trading_system.log"