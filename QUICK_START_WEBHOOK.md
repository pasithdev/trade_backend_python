# 🚀 Quick Start Guide - Pine Script Advanced Webhook

## ✅ All Strategy Files Ready!

**11 Pine Script strategies** now support the **advanced-trading-webhook** endpoint with smart auto-reduction.

---

## 📋 Updated Files (Oct 3, 2025)

✅ **SMC Crypto Scalper 5min.pine**  
✅ **SMC Crypto Scalper 5min - IMPROVED.pine**  
✅ **Crypto Scalper v5.pine**  
✅ **Crypto Scalper v6 - High Profit.pine**

---

## 🎯 Standard JSON Format

All strategies now send this format:

```json
{
    "symbol": "BTCUSDT",
    "action": "buy|sell|close",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```

---

## ⚙️ TradingView Setup (3 Steps)

### 1. Configure Strategy Settings
```
Balance Percentage: 0.10 to 0.25 (10-25%)
Leverage: 5 to 15x
```

### 2. Create Alert
```
Condition: Your strategy signal
Message: {{strategy.order.alert_message}}
Webhook URL: http://your-server/api/binance/advanced-trading-webhook
Frequency: Once Per Bar Close
```

### 3. Test & Deploy
- Click "Test" button
- Verify JSON format
- Start with paper trading

---

## 💡 Recommended Settings

| Strategy | Balance % | Leverage | Best For |
|----------|-----------|----------|----------|
| SMC Scalper | 15-25% | 10-15x | 5min BTC/ETH |
| SMC IMPROVED | 10-20% | 10-20x | 5min All pairs |
| Scalper v5 | 15-25% | 10-15x | 5-15min BTC/ETH |
| Scalper v6 HP | 10-15% | 15-25x | 5-15min High R:R |

---

## 🔧 Webhook Endpoint

**URL:** `/api/binance/advanced-trading-webhook`

**Features:**
- ✅ Auto position sizing
- ✅ Smart auto-reduction  
- ✅ Balance safety (5-10% margin)
- ✅ Symbol auto-detection
- ✅ Close opposite positions

---

## 📚 Documentation

- **PINE_SCRIPT_ALERT_FORMAT_UPDATE.md** - Complete file inventory
- **PINE_SCRIPT_WEBHOOK_UPDATE_SUMMARY.md** - Detailed changes
- **ADVANCED_TRADING_WEBHOOK_GUIDE.md** - Webhook documentation
- **SMART_REDUCTION_GUIDE.md** - Auto-reduction explained

---

## ⚠️ Safety First

1. Start with **10-15% balance** per trade
2. Use **5-10x leverage** initially
3. Test in **paper trading** first
4. Monitor **auto-reduction** behavior
5. Scale up **gradually**

---

## 🎉 Ready to Trade!

All strategies updated, tested, and ready for production deployment.

**Last Updated:** October 3, 2025  
**Status:** ✅ Production Ready
