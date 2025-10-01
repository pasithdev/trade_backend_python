# TradingView Pine Script Integration Guide

## Overview
All three Pine scripts have been updated to work seamlessly with the new Smart Webhook system. They now use simplified alert messages that leverage the smart webhook's default settings (20% quantity, 10x leverage).

## Updated Pine Scripts

### 1. State-aware MA Cross Strategy
- **File**: `State-aware MA Cross-pasith.pine`
- **Strategy**: Moving average crossover with state-aware logic
- **Signals**: Buy on MA cross up, Close on MA cross down or MACD/EMA200 conditions

### 2. Target Trend Strategy
- **File**: `Target_Trend_V1-pasith.pine`  
- **Strategy**: Trend following with ATR-based stops
- **Signals**: Buy on trend up, Sell on trend down

### 3. Professional Crypto Super Scalper
- **File**: `Professional Crypto Super Scalper v2.0.pine`
- **Strategy**: Advanced multi-factor scalping system
- **Signals**: Long/Short based on liquidity, volume, and smart money concepts

## New Alert Message Format

All scripts now use this simplified format:
```json
{"action": "buy", "symbol": "{{ticker}}", "entry": "{{close}}"}
{"action": "sell", "symbol": "{{ticker}}", "entry": "{{close}}"}
{"action": "close", "symbol": "{{ticker}}", "entry": "{{close}}"}
```

## Smart Webhook Benefits

1. **Simplified Setup**: No need to manually configure quantity and leverage in Pine script
2. **Consistent Settings**: All strategies use the same default settings (20% quantity, 10x leverage)
3. **Automatic Conversion**: Smart webhook converts 20% to the exact quantity for each symbol
4. **Error Prevention**: Built-in validation prevents 400 errors from minimum quantity issues

## TradingView Alert Setup

### Step 1: Create Alert
1. Open your Pine script in TradingView
2. Click on "Add Alert" (alarm clock icon)
3. Select your strategy from the Condition dropdown

### Step 2: Configure Webhook
1. **Webhook URL**: `http://your-server:80/api/binance/smart-webhook`
2. **Message**: The alert message is automatically set by the Pine script
3. **Frequency**: "Once Per Bar Close" (recommended)

### Step 3: Alert Settings
For each strategy, set up these alerts:

**State-aware MA Cross:**
- Buy Signal: `{"action": "buy", "symbol": "{{ticker}}", "entry": "{{close}}"}`
- Close Signal: `{"action": "close", "symbol": "{{ticker}}", "entry": "{{close}}"}`

**Target Trend:**
- Buy Signal: `{"action": "buy", "symbol": "{{ticker}}", "entry": "{{close}}"}`
- Sell Signal: `{"action": "sell", "symbol": "{{ticker}}", "entry": "{{close}}"}`

**Super Scalper:**
- Long Entry: `{"action": "buy", "symbol": "{{ticker}}", "entry": "{{close}}"}`
- Short Entry: `{"action": "sell", "symbol": "{{ticker}}", "entry": "{{close}}"}`

## Webhook Endpoints

### Primary Endpoint
```
http://your-server:80/api/binance/smart-webhook
```

### Alternative Endpoint (for TradingView compatibility)
```
http://your-server:80/api/tradingview/binance/smart-webhook
```

## Default Settings Used by Smart Webhook

| Setting | Value | Description |
|---------|-------|-------------|
| Quantity | 20% | Percentage of available balance |
| Leverage | 10x | Futures leverage multiplier |
| Stop Loss | 1.0% | Default stop loss percentage |
| Take Profit | 2.0% | Default take profit percentage |

## Customizing Settings (Optional)

If you want different settings for specific strategies, you can modify the alert message:

```json
{
    "action": "buy",
    "symbol": "{{ticker}}",
    "entry": "{{close}}",
    "quantity_percent": 0.30,
    "leverage": 15,
    "sl_percent": 1.5,
    "tp_percent": 3.0
}
```

## Testing Your Setup

### 1. Test Individual Scripts
Run the test webhook to verify each script works:
```bash
python test_smart_webhook.py
```

### 2. Check Webhook Logs
Monitor your server logs to see incoming webhook calls:
```bash
tail -f trading_system.log
```

### 3. Verify Binance Orders
Check your Binance account for successful order placement.

## Troubleshooting

### Common Issues

1. **400 Errors**: Usually resolved by the smart webhook's automatic quantity validation
2. **Symbol Format**: Webhook automatically adds "USDT" if missing
3. **Minimum Balance**: Webhook shows exactly how much balance is needed

### Error Messages
The smart webhook provides detailed error messages with specific solutions:
- Shows minimum balance required for each symbol
- Suggests alternative quantity percentages
- Provides Binance API error code explanations

## Strategy-Specific Notes

### State-aware MA Cross
- Uses MACD and EMA200 for additional close conditions
- Best for trending markets
- Recommended timeframes: 5M, 15M, 1H

### Target Trend
- Simple trend following with ATR-based stops
- Good for all market conditions
- Recommended timeframes: 15M, 1H, 4H

### Super Scalper
- Complex multi-factor analysis
- Best for volatile, liquid markets
- Recommended timeframes: 1M, 5M, 15M
- Includes advanced features like drawdown protection

## Production Deployment

### 1. Server Configuration
Ensure your server is accessible from TradingView:
```bash
# Check if port 80 is open
netstat -an | findstr :80

# Update firewall if needed
# (Server-specific commands)
```

### 2. SSL Certificate (Recommended)
For production, use HTTPS endpoints:
```
https://your-domain.com/api/binance/smart-webhook
```

### 3. API Key Security
- Use testnet for initial testing
- Ensure proper IP restrictions on Binance API keys
- Enable only necessary permissions (Spot & Futures Trading)

## Summary

The updated Pine scripts now provide:
- ✅ Simplified alert setup
- ✅ Consistent position sizing (20% default)
- ✅ Automatic quantity calculation
- ✅ Built-in error prevention
- ✅ Comprehensive logging
- ✅ Support for all major trading pairs

All three strategies are now ready for seamless integration with your Smart Webhook system!