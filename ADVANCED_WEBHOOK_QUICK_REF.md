# Advanced Trading Webhook - Quick Reference

## 🚀 Quick Start

### Endpoint
```
POST /api/binance/advanced-trading-webhook
```

### JSON Format
```json
{
    "symbol": "BTCUSDT",
    "action": "buy|sell|close",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```

## 📋 Actions

### BUY - Open Long Position
```json
{
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```
✅ Calculates optimal quantity  
✅ Closes existing short positions first  
✅ Opens long position with market order  

### SELL - Open Short Position
```json
{
    "symbol": "ETHUSDT",
    "action": "sell",
    "balance_percentage": 0.20,
    "leverage": 15,
    "entry": 3000.0
}
```
✅ Calculates optimal quantity  
✅ Closes existing long positions first  
✅ Opens short position with market order  

### CLOSE - Exit All Positions
```json
{
    "symbol": "BTCUSDT",
    "action": "close",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```
✅ Closes ALL long positions (if any)  
✅ Closes ALL short positions (if any)  
✅ Cancels pending orders  

## 🎯 TradingView Alert Templates

### Buy Alert
```json
{"symbol": "{{ticker}}USDT", "action": "buy", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

### Sell Alert
```json
{"symbol": "{{ticker}}USDT", "action": "sell", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

### Close Alert
```json
{"symbol": "{{ticker}}USDT", "action": "close", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

## 💰 Position Size Formula

```
Position Value = Account Balance × Balance % × Leverage
Quantity = Position Value ÷ Current Price
```

### Example Calculation
- Balance: $1,000
- Balance %: 25% (0.25)
- Leverage: 10x
- BTC Price: $50,000

```
Position Value = 1,000 × 0.25 × 10 = $2,500
Quantity = 2,500 ÷ 50,000 = 0.05 BTC
```

## ⚙️ Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| symbol | string | Any | Trading pair (e.g., "BTCUSDT") |
| action | string | buy/sell/close | Trading action |
| balance_percentage | float | 0.01-1.0 | 1%-100% of balance |
| leverage | integer | 1-125 | Leverage multiplier |
| entry | float | > 0 | Reference entry price |

## 📊 Risk Levels

| Risk | Balance % | Leverage | Use Case |
|------|-----------|----------|----------|
| Low | 5-10% | 2-5x | Conservative |
| Medium | 10-25% | 5-10x | Standard |
| High | 25-50% | 10-20x | Aggressive |
| Very High | 50%+ | 20x+ | Expert only |

## ✅ Testing

### Test Script
```bash
python test_advanced_webhook.py
```

### cURL Test
```bash
curl -X POST http://localhost:80/api/binance/advanced-trading-webhook \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","action":"buy","balance_percentage":0.1,"leverage":5,"entry":50000}'
```

## 🔧 Common Issues

| Error | Solution |
|-------|----------|
| Insufficient balance | Reduce balance_percentage or add funds |
| Invalid symbol | Use correct Binance Futures symbol |
| Client not configured | Set API credentials via /binance/config |
| Invalid balance % | Use 0.01 to 1.0 (1% to 100%) |

## 📈 Response Examples

### Success
```json
{
    "success": true,
    "message": "Advanced trading order executed: buy 0.025 BTCUSDT",
    "trade": {
        "symbol": "BTCUSDT",
        "action": "buy",
        "quantity": 0.025,
        "leverage": 10,
        "current_price": 50123.45,
        "main_order_id": 123456789
    }
}
```

### Error
```json
{
    "success": false,
    "error": "Binance API error (Code -2010): Insufficient balance",
    "suggestions": ["Increase your account balance or reduce position size"]
}
```

## 🎯 Key Differences from State-Aware Webhook

**Advanced Trading Webhook:**
- General purpose trading
- Explicit buy/sell/close actions
- Direct control over position direction

**State-Aware MA Cross Webhook:**
- Designed for MA Cross strategy
- Same functionality, different naming
- Strategy-specific optimization

Both webhooks:
✅ Auto-calculate position size  
✅ Close opposite positions first  
✅ Support dual-direction trading  
✅ Handle all symbols correctly  

## 📚 Documentation

Full guide: `ADVANCED_TRADING_WEBHOOK_GUIDE.md`  
Pine Script example: `Advanced_Trading_Example.pine`  
Test script: `test_advanced_webhook.py`

## 🔐 Security Notes

✅ Always test with small amounts first  
✅ Use conservative leverage initially  
✅ Monitor positions regularly  
✅ Set appropriate risk per trade  
✅ Keep API credentials secure  

---

**Ready to trade? Start with conservative settings and scale up gradually!**
