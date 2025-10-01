# Pine Script Webhook Payload Update Summary

## Updated Payload Format

All Pine Scripts have been updated to use the new webhook payload format:

```json
{
  "symbol": "BTCUSDT",
  "action": "buy",         // or "sell" or "close"
  "balance_percentage": 0.50,
  "leverage": 10,
  "entry": 43000
}
```

## Updated Pine Scripts

### 1. Professional Crypto Super Scalper v2.0.pine

**New Features Added:**
- `input_balance_percentage` - Configurable balance percentage (default: 0.50 = 50%)
- `input_leverage` - Configurable leverage (default: 20)

**Alert Messages:**
- **Buy Signal**: `{"symbol": "BTCUSDT", "action": "buy", "balance_percentage": 0.50, "leverage": 20, "entry": 43000}`
- **Sell Signal**: `{"symbol": "BTCUSDT", "action": "sell", "balance_percentage": 0.50, "leverage": 20, "entry": 43000}`
- **Emergency Exit**: `{"symbol": "BTCUSDT", "action": "close", "balance_percentage": 0.50, "leverage": 20, "entry": 43000}`

### 2. State-aware MA Cross-pasith.pine

**Existing Settings Used:**
- `quantity` - Order Quantity (% of equity) - maps to balance_percentage
- `leverage` - Leverage setting

**Alert Messages:**
- **Buy Signal**: `{"symbol": "BTCUSDT", "action": "buy", "balance_percentage": 0.20, "leverage": 10, "entry": 43000}`
- **Close Signal**: `{"symbol": "BTCUSDT", "action": "close", "balance_percentage": 0.20, "leverage": 10, "entry": 43000}`

### 3. Target_Trend_V1-pasith.pine

**Existing Settings Used:**
- `quantity` - Order Quantity (% of equity) - maps to balance_percentage  
- `leverage` - Leverage setting

**Alert Messages:**
- **Buy Signal**: `{"symbol": "BTCUSDT", "action": "buy", "balance_percentage": 0.20, "leverage": 10, "entry": 43000}`
- **Sell Signal**: `{"symbol": "BTCUSDT", "action": "sell", "balance_percentage": 0.20, "leverage": 10, "entry": 43000}`

## Webhook Endpoints That Support This Format

✅ **Working Endpoints:**
- `POST /api/binance/state-aware-ma-cross-webhook`
- `POST /api/binance/smart-webhook`
- `POST /api/binance/super-scalper-webhook`
- `POST /api/binance/target-trend-webhook`
- `POST /api/integration/tradingview-to-binance`

## Configuration Guidelines

### Balance Percentage Requirements
- **Minimum for BTCUSDT**: ~37.3% (depends on current BTC price)
- **Recommended**: 40-50% for reliable execution
- **Maximum**: 100% (1.0)

### Leverage Settings
- **Conservative**: 10x leverage
- **Moderate**: 20x leverage  
- **Aggressive**: 50x+ leverage (higher risk)

### Symbol Requirements
- Use exact Binance futures symbols (e.g., "BTCUSDT", "ETHUSDT")
- System will auto-append "USDT" if missing

## Example TradingView Alert Setup

1. **Create Alert**: Choose your Pine Script
2. **Message**: Use the built-in alert messages (they now generate the correct JSON)
3. **Webhook URL**: `http://167.71.207.209/api/binance/state-aware-ma-cross-webhook`
4. **Once Per Bar Close**: Recommended to avoid multiple signals

## Testing

Run the comprehensive test script:
```bash
python test_all_webhooks.py
```

This will test all endpoints with various balance percentages and show minimum requirements.

## Important Notes

⚠️ **Production Ready**: All webhooks are now working with the new format
⚠️ **Balance Limits**: Ensure sufficient balance percentage for your chosen symbol
⚠️ **Rate Limiting**: TradingView webhooks have rate limits - use "Once Per Bar Close"
⚠️ **Risk Management**: Start with smaller balance percentages and lower leverage

## Migration Checklist

- [x] Update Professional Crypto Super Scalper v2.0
- [x] Update State-aware MA Cross Strategy  
- [x] Update Target Trend V1 Strategy
- [x] Create comprehensive test script
- [x] Verify webhook endpoints compatibility
- [x] Document new payload format
- [x] Test minimum balance requirements

All Pine Scripts are now compatible with your webhook system! 🚀