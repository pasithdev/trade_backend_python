# TradingView Pine Script to Binance Integration Guide

## Overview
This guide shows how to connect TradingView Pine Script signals to automatically execute trades on Binance with take profit and stop loss orders.

## Architecture
```
Pine Script (TradingView) → Webhook Alert → Your Backend → Binance API (with TP/SL)
```

## Step 1: Configure Your Backend System

### 1.1 Start Your Backend Server
```bash
cd /path/to/your/backend
python -m flask run --host=0.0.0.0 --port=5000
```

### 1.2 Configure Binance API Credentials
```bash
curl -X POST http://localhost:5000/api/binance/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_binance_api_key",
    "api_secret": "your_binance_api_secret",
    "testnet": true,
    "tp_percentage": 2.0,
    "sl_percentage": 1.0,
    "min_order_value": 10.0,
    "max_order_value": 1000.0
  }'
```

### 1.3 Enable Automatic Trading
```bash
curl -X POST http://localhost:5000/api/tradingview/auto-trading/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "require_tp_sl": true,
    "max_daily_trades": 10
  }'
```

## Step 2: Make Your Backend Accessible

### Option A: Local Testing with ngrok
```bash
# Install ngrok (if not installed)
npm install -g ngrok

# Create public URL for your local server
ngrok http 5000
```
This gives you a public URL like: `https://abc123.ngrok.io`

### Option B: Deploy to Cloud
Deploy your backend to:
- **Heroku**: `https://your-app.herokuapp.com`
- **Railway**: `https://your-app.railway.app`
- **DigitalOcean**: `https://your-domain.com`
- **AWS/GCP**: Configure your own domain

## Step 3: Set Up Pine Script in TradingView

### 3.1 Create Your Strategy
1. Open TradingView
2. Go to Pine Editor
3. Copy the provided `pine_script_example.pine` code
4. Modify the webhook URL to your backend:
   ```pine
   webhookUrl = input.string("https://your-domain.com/api/tradingview/webhook", "Webhook URL")
   ```
5. Save and add to chart

### 3.2 Configure Alert Settings
1. Click "Create Alert" button
2. Set Condition to your strategy
3. **Important**: In the "Notifications" tab:
   - ✅ Enable "Webhook URL"
   - Enter your webhook URL: `https://your-domain.com/api/tradingview/webhook`
4. In "Message" field, use the dynamic message from Pine Script (leave default)

## Step 4: Webhook Message Format

Your Pine Script will send JSON like this:

### Long (Buy) Signal
```json
{
  "symbol": "BTCUSDT",
  "action": "buy", 
  "price": 50000.00,
  "tp": 51000.00,
  "sl": 49500.00,
  "quantity": 0.001,
  "message": "Long entry signal from Pine Script"
}
```

### Short (Sell) Signal
```json
{
  "symbol": "BTCUSDT",
  "action": "sell",
  "price": 50000.00, 
  "tp": 49000.00,
  "sl": 50500.00,
  "quantity": 0.001,
  "message": "Short entry signal from Pine Script"
}
```

## Step 5: How It Works

1. **Pine Script Detection**: Your strategy detects entry conditions
2. **Webhook Alert**: TradingView sends JSON to your webhook
3. **Backend Processing**: Your system validates and processes the alert
4. **Binance Execution**: 
   - Places market order (buy/sell)
   - Immediately places OCO order with exact TP/SL prices
5. **Order Management**: Tracks active orders and executions

## Step 6: Testing Your Setup

### Test the Webhook Endpoint
```bash
curl -X POST https://your-domain.com/api/tradingview/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "action": "buy",
    "price": 45000,
    "tp": 45900,
    "sl": 44550,
    "quantity": 0.001,
    "message": "Test alert"
  }'
```

### Check Alert History
```bash
curl -X GET https://your-domain.com/api/tradingview/alerts
```

### View Active Orders
```bash
curl -X GET https://your-domain.com/api/binance/orders
```

## Step 7: Important Safety Features

Your system includes these safety features:

### ✅ Validation
- Validates all webhook data
- Checks symbol format
- Verifies TP/SL prices

### ✅ Risk Management
- Daily trade limits
- Min/max order values
- Testnet support

### ✅ Order Management
- Uses Binance OCO orders for TP/SL
- Exact price execution (no percentage modification)
- Proper order precision handling

## Step 8: Pine Script Customization

### Modify Entry Conditions
```pine
// Example: Add moving average filter
longCondition = ta.crossover(rsi, rsiOversold) and close > ta.sma(close, 50)
shortCondition = ta.crossunder(rsi, rsiOverbought) and close < ta.sma(close, 50)
```

### Adjust Risk Parameters
```pine
tpPercent = input.float(2.0, "Take Profit %")  // 2% TP
slPercent = input.float(1.0, "Stop Loss %")    // 1% SL
quantity = input.float(0.001, "Trade Quantity") // Trade size
```

### Multiple Symbols
Create separate alerts for each symbol you want to trade:
- BTCUSDT
- ETHUSDT  
- ADAUSDT
- etc.

## Step 9: Monitoring and Logs

### Check System Status
```bash
curl -X GET https://your-domain.com/api/tradingview/auto-trading/config
```

### Monitor Trades
- Check the backend logs
- Use trading_system.log file
- Monitor Binance account directly

## Troubleshooting

### Common Issues:
1. **Webhook not receiving**: Check firewall and URL
2. **Invalid JSON**: Verify Pine Script message format
3. **Binance errors**: Check API credentials and permissions
4. **Order precision**: System handles this automatically

### Debug Mode:
Set `testnet: true` in Binance config for safe testing.

## Security Notes
- Use testnet for initial testing
- Never commit API keys to code
- Use environment variables for sensitive data
- Implement proper authentication for production
