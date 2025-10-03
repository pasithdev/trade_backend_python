# Alert System Guide - Intelligent Crypto Scalper v1.0

## Overview

I've added a comprehensive alert system to the Intelligent Crypto Scalper strategy, similar to the Target_Trend format you provided. The system sends JSON-formatted webhook messages that can be used with trading bots and automation systems.

---

## New Features Added

### 1. Alert Input Parameters

**New Input Group: "Alert Settings"**
- ✅ **Enable Alerts**: Toggle alerts on/off
- ✅ **Order Quantity**: Percentage of equity (0.01-1.0, default: 0.20 = 20%)
- ✅ **Leverage**: Leverage multiplier (1-125, default: 10x)

### 2. JSON Alert Messages

**Buy Alert Format:**
```json
{
  "symbol": "BTCUSDT",
  "action": "buy", 
  "balance_percentage": 0.20,
  "leverage": 10,
  "entry": 43250.50
}
```

**Sell Alert Format:**
```json
{
  "symbol": "BTCUSDT",
  "action": "sell",
  "balance_percentage": 0.20, 
  "leverage": 10,
  "entry": 43180.25
}
```

### 3. Alert Triggers

**Realistic Signals** (Primary):
- Fires when `realistic_long_signal` or `realistic_short_signal` is true
- Only triggers when bar is confirmed (`barstate.isconfirmed`)
- Uses `alert.freq_once_per_bar` to prevent spam

**Complex Signals** (Backup):
- Also fires for original complex signals (`enter_long_controlled`/`enter_short_controlled`)
- Rarely triggers due to strict conditions

### 4. Debug Status Table

**New Debug Table** (top-left corner):
- Market Condition (Choppy/Tradeable)
- Current RSI value
- Momentum scores (Long/Short)
- Can Trade status
- Active signal status

---

## How to Use Alerts

### Step 1: Enable Alerts
1. Open strategy settings in TradingView
2. Go to "Alert Settings" group
3. Check "Enable Alerts" ✅
4. Set desired "Order Quantity" (default 20% = 0.20)
5. Set desired "Leverage" (default 10x)

### Step 2: Create TradingView Alert
1. Right-click on chart → "Add Alert"
2. **Condition**: Select your strategy name
3. **Alert Actions**: Choose "Webhook URL" if using automation
4. **Message**: Leave default (will use JSON format)
5. **Options**: 
   - ✅ "Once Per Bar Close" (recommended)
   - ✅ "Only Once" (if you want single alerts)

### Step 3: Webhook Integration (Optional)
If using trading bots or automation:
1. Set webhook URL in alert settings
2. The JSON message will be sent automatically
3. Your bot can parse the JSON and execute trades

---

## Alert Message Fields Explained

| Field | Description | Example |
|-------|-------------|---------|
| `symbol` | Trading pair from chart | "BTCUSDT" |
| `action` | Trade direction | "buy" or "sell" |
| `balance_percentage` | % of equity to use | 0.20 (20%) |
| `leverage` | Leverage multiplier | 10 |
| `entry` | Entry price | 43250.50 |

---

## Alert Frequency

### Expected Alert Frequency:
- **Trending Markets**: 5-15 alerts per day
- **Choppy Markets**: 0-3 alerts per day (filtered out)
- **Volatile Markets**: 10-25 alerts per day

### Alert Quality:
- ✅ **Confirmed Signals**: Only fires on bar close
- ✅ **Volume Filtered**: Requires above-average volume
- ✅ **RSI Filtered**: Avoids extreme overbought/oversold
- ✅ **Momentum Confirmed**: Requires directional momentum
- ✅ **Market Filtered**: Avoids choppy conditions

---

## Webhook Automation Examples

### Example 1: 3Commas Bot
```json
{
  "message_type": "bot",
  "bot_id": 12345,
  "email_token": "your-token",
  "delay_seconds": 0,
  "pair": "USDT_BTC"
}
```

### Example 2: Custom Bot
```python
import json
import requests

def handle_webhook(data):
    alert = json.loads(data)
    
    if alert['action'] == 'buy':
        # Execute buy order
        place_order(
            symbol=alert['symbol'],
            side='BUY',
            quantity=calculate_quantity(alert['balance_percentage']),
            leverage=alert['leverage']
        )
    elif alert['action'] == 'sell':
        # Execute sell order
        place_order(
            symbol=alert['symbol'], 
            side='SELL',
            quantity=calculate_quantity(alert['balance_percentage']),
            leverage=alert['leverage']
        )
```

---

## Testing Alerts

### Step 1: Test Alert Creation
1. Create a test alert with "Show popup" enabled
2. Wait for signals to appear on chart
3. Verify popup shows JSON message

### Step 2: Test Webhook (if using)
1. Use a webhook testing service (webhook.site)
2. Set test URL in alert
3. Verify JSON is received correctly

### Step 3: Validate Signal Quality
1. Check debug table shows correct status
2. Verify signals align with good entry points
3. Monitor alert frequency matches expectations

---

## Troubleshooting

### Issue 1: No Alerts Firing
**Possible Causes:**
- Alerts not enabled in settings
- Market too choppy (check debug table)
- No signals being generated

**Solutions:**
- Enable "Enable Alerts" in settings
- Check debug table for signal status
- Try more volatile market/timeframe

### Issue 2: Too Many Alerts
**Possible Causes:**
- Very volatile market
- RSI thresholds too wide

**Solutions:**
- Reduce alert quantity
- Tighten RSI thresholds (75/25 → 70/30)
- Add additional filters

### Issue 3: Webhook Not Working
**Possible Causes:**
- Incorrect webhook URL
- JSON format issues
- Bot configuration problems

**Solutions:**
- Test webhook URL manually
- Verify JSON format in alert message
- Check bot documentation

---

## Alert Settings Recommendations

### Conservative Trading:
```
Order Quantity: 0.10 (10%)
Leverage: 5x
Enable Alerts: Yes
```

### Moderate Trading:
```
Order Quantity: 0.20 (20%) 
Leverage: 10x
Enable Alerts: Yes
```

### Aggressive Trading:
```
Order Quantity: 0.30 (30%)
Leverage: 20x
Enable Alerts: Yes
```

---

## Integration with Popular Platforms

### TradingView Alerts → 3Commas
1. Create 3Commas bot
2. Get webhook URL from 3Commas
3. Set webhook in TradingView alert
4. Bot executes trades automatically

### TradingView Alerts → Binance API
1. Create custom webhook server
2. Parse JSON alerts
3. Use Binance API to execute trades
4. Implement risk management

### TradingView Alerts → Discord/Telegram
1. Create Discord/Telegram webhook
2. Format JSON as readable message
3. Send notifications to channel
4. Manual trade execution

---

## Security Considerations

### API Key Safety:
- Never include API keys in alert messages
- Use server-side API key storage
- Implement IP whitelisting

### Webhook Security:
- Use HTTPS webhooks only
- Implement webhook signature verification
- Add rate limiting to prevent abuse

### Risk Management:
- Set maximum position sizes
- Implement daily loss limits
- Add manual override capabilities

---

## Status

**Alert System Status**: ✅ **FULLY IMPLEMENTED**

**Features Added**:
- ✅ JSON alert messages
- ✅ Configurable quantity and leverage
- ✅ Bar confirmation requirement
- ✅ Debug status table
- ✅ Webhook-ready format
- ✅ Multiple signal types

**Ready For**:
- TradingView alert creation
- Webhook automation
- Trading bot integration
- Manual trading signals

---

**Created**: October 2, 2025  
**Based On**: Target_Trend_V1-pasith.pine format  
**Compatible With**: TradingView alerts, webhooks, trading bots  
**Status**: Production ready