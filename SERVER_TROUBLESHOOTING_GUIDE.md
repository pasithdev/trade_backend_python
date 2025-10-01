# Server Troubleshooting Guide for 167.71.207.209

## 🔐 **SECURITY WARNING**
**Never share server credentials publicly!** The information you provided should be kept secure.

## 🚀 **Quick Diagnostic Steps**

### **1. Connect to Your Server**
```bash
# SSH to your server (replace with your actual method)
ssh root@167.71.207.209

# Or if using PuTTY on Windows:
# Host: 167.71.207.209
# Username: root
# Password: [your password]
```

### **2. Check Application Status**
```bash
# Check if Python application is running
ps aux | grep python
ps aux | grep main.py

# Check for multiple processes (common cause of intermittent issues)
ps aux | grep -c python

# Check application logs
tail -f trading_system.log
tail -f /var/log/gunicorn/error.log
tail -f /var/log/nginx/error.log
```

### **3. Check System Resources**
```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check CPU usage
top -n 1

# Check network connections
netstat -tlnp | grep :80
netstat -tlnp | grep python
```

### **4. Test Local Webhook (on server)**
```bash
# Test webhook locally on server
curl -X POST http://localhost/api/binance/state-aware-ma-cross-webhook \
  -H "Content-Type: application/json" \
  -d '{"symbol": "ETHUSDT", "action": "buy", "balance_percentage": 0.25, "leverage": 10, "entry": 2456.78}'

# Check API configuration
curl http://localhost/api/binance/status
```

### **5. Check Application Logs for Specific Errors**
```bash
# Look for 400 errors in logs
grep -n "400" trading_system.log
grep -n "error" trading_system.log
grep -n "minimum quantity" trading_system.log
grep -n "Binance" trading_system.log

# Check recent log entries (last 50 lines)
tail -50 trading_system.log
```

## 🛠 **Common Causes of Intermittent 400 Errors**

### **1. Multiple Application Instances**
```bash
# Kill all Python processes
pkill -f main.py
pkill -f python

# Start fresh
cd /path/to/your/app
python src/main.py &
```

### **2. API Configuration Issues**
```bash
# Check if API credentials are set
curl -X GET http://localhost/api/binance/status

# Reconfigure API if needed
curl -X POST http://localhost/api/binance/config \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_key", "api_secret": "your_secret", "testnet": false}'
```

### **3. Memory/Resource Exhaustion**
```bash
# Restart the application service
systemctl restart your-app-service  # if using systemd
# OR
pm2 restart all  # if using PM2
# OR kill and restart manually
```

### **4. File Permission Issues**
```bash
# Check file permissions
ls -la trading_system.log
ls -la src/

# Fix permissions if needed
chmod 755 src/
chmod 644 trading_system.log
```

## 📊 **Monitoring Commands**

### **Real-time Log Monitoring**
```bash
# Monitor logs in real-time
tail -f trading_system.log | grep -E "(ERROR|400|Exception)"

# Monitor system resources
watch -n 1 'free -h && echo "---" && ps aux | head -10'
```

### **Test Webhook Performance**
```bash
# Simple webhook test loop
for i in {1..10}; do
  echo "Test $i:"
  curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
    -X POST http://localhost/api/binance/state-aware-ma-cross-webhook \
    -H "Content-Type: application/json" \
    -d '{"symbol": "ETHUSDT", "action": "buy", "balance_percentage": 0.25, "leverage": 10, "entry": 2456.78}'
  sleep 1
done
```

## 🔧 **Quick Fixes**

### **Fix 1: Restart Application**
```bash
# Find and kill existing processes
pkill -f main.py
sleep 2

# Start fresh
cd /your/app/directory
nohup python src/main.py > app.log 2>&1 &
```

### **Fix 2: Clear Logs and Start Fresh**
```bash
# Backup old logs
mv trading_system.log trading_system.log.backup

# Start with clean logs
touch trading_system.log
python src/main.py
```

### **Fix 3: Check and Fix API Configuration**
```bash
# Test API configuration
curl -X POST http://localhost/api/binance/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ",
    "api_secret": "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF",
    "testnet": false
  }'
```

## 📈 **Performance Optimization**

### **Add Process Monitoring**
```bash
# Install htop for better process monitoring
apt update && apt install htop

# Use htop to monitor in real-time
htop
```

### **Set Up Log Rotation**
```bash
# Prevent logs from growing too large
cat > /etc/logrotate.d/trading-app << EOF
/path/to/trading_system.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    create 644 root root
}
EOF
```

## 🚨 **Emergency Recovery**

If the server is completely unresponsive:

```bash
# 1. Reboot the server
sudo reboot

# 2. After reboot, restart services
systemctl start nginx  # if using nginx
cd /your/app/path
python src/main.py &

# 3. Test immediately
curl http://localhost/api/binance/status
```

---

## 📞 **Next Steps**

1. **Run the diagnostic script** I created: `python test_production_server.py`
2. **SSH into your server** and run the commands above
3. **Check the specific error patterns** in your logs
4. **Report back** with the log outputs so I can help identify the exact issue

The intermittent 400 errors are likely caused by one of:
- Multiple application instances running
- API credentials getting reset/lost
- Memory/resource exhaustion
- Race conditions in request handling

Let me know what you find in the logs!