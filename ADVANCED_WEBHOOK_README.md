# 🎯 Advanced Trading Webhook - New Feature

## ✅ Implementation Complete!

A new powerful webhook endpoint has been created for intelligent position management with automatic margin and quantity calculation.

---

## 📁 Quick Access

### Documentation
- **📘 Complete Guide:** [ADVANCED_TRADING_WEBHOOK_GUIDE.md](ADVANCED_TRADING_WEBHOOK_GUIDE.md)
- **⚡ Quick Reference:** [ADVANCED_WEBHOOK_QUICK_REF.md](ADVANCED_WEBHOOK_QUICK_REF.md)
- **📋 Implementation Details:** [ADVANCED_WEBHOOK_IMPLEMENTATION.md](ADVANCED_WEBHOOK_IMPLEMENTATION.md)

### Code & Examples
- **🔧 Test Script:** [test_advanced_webhook.py](test_advanced_webhook.py)
- **📊 Pine Script Example:** [Advanced_Trading_Example.pine](Advanced_Trading_Example.pine)
- **💻 Main Code:** `src/routes/binance_trading.py` (line ~2036)

---

## 🚀 Quick Start

### 1. Endpoint URL
```
POST /api/binance/advanced-trading-webhook
```

### 2. JSON Message
```json
{
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```

### 3. Test It
```bash
python test_advanced_webhook.py
```

---

## 🎯 What It Does

### BUY Action
- ✅ Calculates optimal position size automatically
- ✅ Closes existing SHORT positions first
- ✅ Opens LONG position with market order

### SELL Action
- ✅ Calculates optimal position size automatically
- ✅ Closes existing LONG positions first
- ✅ Opens SHORT position with market order

### CLOSE Action
- ✅ Closes ALL positions (long & short) for the symbol
- ✅ Cancels pending orders
- ✅ Returns detailed closure information

---

## 💡 Key Features

| Feature | Description |
|---------|-------------|
| **Auto Position Sizing** | Calculates quantity: `(Balance × % × Leverage) / Price` |
| **Smart Management** | Closes opposite positions automatically |
| **Dual Direction** | Supports both long and short positions |
| **Symbol Compatible** | Works with all Binance Futures USDT pairs |
| **Error Handling** | Comprehensive validation and helpful messages |
| **TradingView Ready** | Direct integration with Pine Script alerts |

---

## 📊 Actions Supported

| Action | What Happens | Example |
|--------|--------------|---------|
| `buy` | Open long position | `{"action": "buy", ...}` |
| `sell` | Open short position | `{"action": "sell", ...}` |
| `close` | Close all positions | `{"action": "close", ...}` |

---

## 🎯 TradingView Alert Templates

### Buy
```json
{"symbol": "{{ticker}}USDT", "action": "buy", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

### Sell
```json
{"symbol": "{{ticker}}USDT", "action": "sell", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

### Close
```json
{"symbol": "{{ticker}}USDT", "action": "close", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

---

## 📈 Position Size Example

**Parameters:**
- Balance: $1,000
- Balance %: 25% (0.25)
- Leverage: 10x
- BTC Price: $50,000

**Calculation:**
```
Position Value = 1,000 × 0.25 × 10 = $2,500
Quantity = 2,500 ÷ 50,000 = 0.05 BTC
```

---

## 🧪 Testing

### Run Tests
```bash
# Run comprehensive test suite
python test_advanced_webhook.py
```

### Manual Test with cURL
```bash
# Test buy action
curl -X POST http://localhost:80/api/binance/advanced-trading-webhook \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","action":"buy","balance_percentage":0.1,"leverage":5,"entry":50000}'
```

---

## 🔒 Risk Management

| Risk Level | Balance % | Leverage | Description |
|------------|-----------|----------|-------------|
| Low | 5-10% | 2-5x | Conservative |
| Medium | 10-25% | 5-10x | Balanced |
| High | 25-50% | 10-20x | Aggressive |
| Very High | 50%+ | 20x+ | Expert only |

**⚠️ Always start with small amounts and conservative settings!**

---

## ✅ Next Steps

1. **Test the webhook:** `python test_advanced_webhook.py`
2. **Review documentation:** Read the complete guide
3. **Try Pine Script:** Load the example strategy
4. **Create alerts:** Set up TradingView alerts
5. **Start trading:** Begin with small positions

---

## 📚 Full Documentation

### Complete Guide
For detailed information including:
- Response formats
- Error handling
- Position calculations
- TradingView integration
- Security best practices

**Read:** [ADVANCED_TRADING_WEBHOOK_GUIDE.md](ADVANCED_TRADING_WEBHOOK_GUIDE.md)

### Quick Reference
For quick lookup of:
- Common actions
- Alert templates
- Parameter ranges
- Troubleshooting

**Read:** [ADVANCED_WEBHOOK_QUICK_REF.md](ADVANCED_WEBHOOK_QUICK_REF.md)

---

## 🎉 Ready to Use!

The webhook is fully implemented, tested, and documented. Start with conservative settings and scale up as you gain confidence!

**Happy Trading! 🚀**
