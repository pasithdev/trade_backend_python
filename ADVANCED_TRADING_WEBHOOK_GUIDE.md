# Advanced Trading Webhook Guide

## 🚀 Overview

The **Advanced Trading Webhook** is a powerful endpoint that provides intelligent position management for Binance Futures trading with automatic margin and quantity calculation.

## 📍 Endpoint URLs

### Primary Endpoint
```
POST /api/binance/advanced-trading-webhook
```

### Alternative Endpoint (TradingView Compatible)
```
POST /api/tradingview/binance/advanced-trading-webhook
```

## 🎯 Key Features

✅ **Automatic Position Sizing** - Calculates optimal quantity based on balance percentage and leverage  
✅ **Smart Position Management** - Automatically closes opposite positions before opening new ones  
✅ **Dual Direction Trading** - Supports both long (buy) and short (sell) positions  
✅ **Flexible Close Actions** - Close all positions for a specific symbol  
✅ **Symbol Compatibility** - Respects minimum quantity and precision requirements  
✅ **Comprehensive Error Handling** - Detailed error messages and suggestions  
✅ **Real-time Calculation** - Uses current market price and account balance  

## 📊 JSON Message Format

### Standard Format
```json
{
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```

### Parameters

| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| `symbol` | string | ✅ Yes | Trading pair symbol | "BTCUSDT", "ETHUSDT", etc. |
| `action` | string | ✅ Yes | Trading action to execute | "buy", "sell", "close" |
| `balance_percentage` | float | ✅ Yes* | Percentage of balance to use | 0.01 - 1.0 (1% - 100%) |
| `leverage` | integer | ✅ Yes | Leverage multiplier | 1 - 125 (depends on symbol) |
| `entry` | float | ⚠️ Optional | Entry price reference | Any positive number |

*Required for `buy` and `sell` actions, ignored for `close` action

## 🔧 Action Types

### 1. BUY Action (Long Position)

Opens a long position with automatic quantity calculation.

**Example:**
```json
{
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```

**What Happens:**
1. Calculates position size: `(Account Balance * 0.25 * 10) / Current Price`
2. Closes any existing SHORT positions for BTCUSDT
3. Sets leverage to 10x
4. Places MARKET BUY order
5. Returns order details and calculation breakdown

### 2. SELL Action (Short Position)

Opens a short position with automatic quantity calculation.

**Example:**
```json
{
    "symbol": "ETHUSDT",
    "action": "sell",
    "balance_percentage": 0.20,
    "leverage": 15,
    "entry": 3000.0
}
```

**What Happens:**
1. Calculates position size: `(Account Balance * 0.20 * 15) / Current Price`
2. Closes any existing LONG positions for ETHUSDT
3. Sets leverage to 15x
4. Places MARKET SELL order
5. Returns order details and calculation breakdown

### 3. CLOSE Action (Exit All Positions)

Closes ALL positions (both long and short) for the specified symbol.

**Example:**
```json
{
    "symbol": "BTCUSDT",
    "action": "close",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
}
```

**What Happens:**
1. Checks for all open positions on BTCUSDT
2. Closes LONG positions with MARKET SELL orders
3. Closes SHORT positions with MARKET BUY orders
4. Cancels any pending orders for the symbol
5. Returns details of all closed positions

## 💡 Usage Examples

### Example 1: Conservative Long Entry
```json
{
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.10,
    "leverage": 5,
    "entry": 43000.0
}
```
Uses 10% of balance with 5x leverage for a conservative long position.

### Example 2: Aggressive Short Entry
```json
{
    "symbol": "ETHUSDT",
    "action": "sell",
    "balance_percentage": 0.50,
    "leverage": 20,
    "entry": 2500.0
}
```
Uses 50% of balance with 20x leverage for an aggressive short position.

### Example 3: Exit All Positions
```json
{
    "symbol": "BTCUSDT",
    "action": "close",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 45000.0
}
```
Closes all BTCUSDT positions regardless of direction.

## 📈 Response Format

### Success Response (Buy/Sell)
```json
{
    "success": true,
    "message": "Advanced trading order executed: buy 0.025 BTCUSDT",
    "trade": {
        "symbol": "BTCUSDT",
        "action": "buy",
        "quantity": 0.025,
        "leverage": 10,
        "entry_price": 50000.0,
        "current_price": 50123.45,
        "main_order_id": 123456789,
        "opposite_position_closed": "Closed short position SELL 0.020 BTCUSDT",
        "mode": "auto_quantity",
        "note": "Quantity auto-calculated based on account balance percentage"
    },
    "calculation_details": {
        "account_balance_usdt": 1000.0,
        "balance_percentage": 0.25,
        "leverage": 10,
        "position_value_usdt": 2500.0,
        "current_price": 50123.45,
        "raw_quantity": 0.0498765,
        "quantity": 0.025,
        "symbol_info": {
            "min_qty": 0.001,
            "max_qty": 1000,
            "step_size": 0.001
        }
    },
    "timestamp": "2025-10-03T10:30:45.123456"
}
```

### Success Response (Close)
```json
{
    "success": true,
    "message": "All positions closed for BTCUSDT",
    "symbol": "BTCUSDT",
    "action": "close",
    "closed_positions": [
        {
            "quantity": 0.025,
            "order_id": 123456789,
            "side": "SELL",
            "position_type": "long"
        }
    ],
    "cancelled_orders": [987654321],
    "timestamp": "2025-10-03T10:30:45.123456"
}
```

### Error Response
```json
{
    "success": false,
    "error": "Binance API error (Code -2010): Insufficient balance",
    "suggestions": [
        "Increase your account balance or reduce position size"
    ],
    "webhook_data": {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.90,
        "leverage": 50,
        "entry": 50000.0
    }
}
```

## 🎯 Position Size Calculation

The webhook automatically calculates the optimal quantity:

```
Position Value (USDT) = Account Balance × Balance Percentage × Leverage
Quantity = Position Value ÷ Current Market Price
```

**Example:**
- Account Balance: $1,000 USDT
- Balance Percentage: 25% (0.25)
- Leverage: 10x
- Current BTC Price: $50,000

```
Position Value = 1000 × 0.25 × 10 = 2,500 USDT
Quantity = 2,500 ÷ 50,000 = 0.05 BTC
```

## ⚙️ TradingView Integration

### Pine Script Alert Message

For Buy Signal:
```json
{"symbol": "{{ticker}}", "action": "buy", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

For Sell Signal:
```json
{"symbol": "{{ticker}}", "action": "sell", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

For Close Signal:
```json
{"symbol": "{{ticker}}", "action": "close", "balance_percentage": 0.25, "leverage": 10, "entry": {{close}}}
```

### Alert Configuration

1. **Condition**: Select your strategy condition (e.g., Buy Signal, Sell Signal)
2. **Alert name**: "Advanced Trading - Buy BTCUSDT"
3. **Message**: Use the JSON format above
4. **Webhook URL**: `http://your-server/api/binance/advanced-trading-webhook`
5. **Frequency**: "Once Per Bar Close"

## 🔒 Security & Best Practices

### Risk Management
- ✅ Start with small balance percentages (10-20%)
- ✅ Use conservative leverage (5-10x) for beginners
- ✅ Test with small amounts before production use
- ✅ Monitor positions regularly
- ✅ Set appropriate stop-loss levels

### Balance Percentage Guidelines

| Risk Level | Balance % | Leverage | Risk Profile |
|------------|-----------|----------|--------------|
| Conservative | 5-10% | 2-5x | Low risk, stable |
| Moderate | 10-25% | 5-10x | Medium risk |
| Aggressive | 25-50% | 10-20x | High risk |
| Very Aggressive | 50%+ | 20x+ | Very high risk |

### Symbol Compatibility
- ✅ Works with all Binance Futures USDT pairs
- ✅ Automatically respects minimum quantity requirements
- ✅ Handles precision and step size correctly
- ✅ Validates symbol before placing orders

## 🧪 Testing

### Test Script
Use the provided test script:
```bash
python test_advanced_webhook.py
```

### Manual Testing with cURL

**Buy Test:**
```bash
curl -X POST http://localhost:80/api/binance/advanced-trading-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.10,
    "leverage": 5,
    "entry": 50000.0
  }'
```

**Sell Test:**
```bash
curl -X POST http://localhost:80/api/binance/advanced-trading-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETHUSDT",
    "action": "sell",
    "balance_percentage": 0.15,
    "leverage": 10,
    "entry": 3000.0
  }'
```

**Close Test:**
```bash
curl -X POST http://localhost:80/api/binance/advanced-trading-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "action": "close",
    "balance_percentage": 0.25,
    "leverage": 10,
    "entry": 50000.0
  }'
```

## ❗ Common Errors & Solutions

### Error: "Insufficient balance"
**Solution:** Reduce `balance_percentage` or add more funds to your account

### Error: "Invalid quantity precision"
**Solution:** The webhook automatically handles this - if you see this error, check symbol requirements

### Error: "Binance client not configured"
**Solution:** Ensure API credentials are set via `/binance/config` endpoint

### Error: "Invalid balance_percentage"
**Solution:** Use values between 0.01 (1%) and 1.0 (100%)

### Error: "Market price moved too much"
**Solution:** Retry the webhook call - market conditions changed

## 📊 Monitoring & Logging

All webhook activities are logged with:
- Request details (symbol, action, parameters)
- Calculation breakdowns
- Order execution results
- Error messages and suggestions
- Timestamps for audit trail

Check logs for troubleshooting:
```bash
tail -f trading_system.log
```

## 🔄 Comparison with State-Aware Webhook

| Feature | Advanced Trading Webhook | State-Aware MA Cross Webhook |
|---------|-------------------------|------------------------------|
| Buy Action | ✅ Yes | ✅ Yes |
| Sell Action | ✅ Yes | ✅ Yes (as short) |
| Close Action | ✅ Closes all positions | ✅ Closes all positions |
| Auto Position Sizing | ✅ Yes | ✅ Yes |
| Close Opposite First | ✅ Yes | ✅ Yes |
| Balance Percentage | ✅ Configurable | ✅ Configurable |
| Leverage Control | ✅ Configurable | ✅ Configurable |
| Use Case | General trading | MA Cross strategy |

## 📞 Support

For issues or questions:
1. Check the error message and suggestions
2. Review the logs for detailed information
3. Verify API credentials are configured
4. Test with small amounts first
5. Check Binance API status

## 🎉 Summary

The Advanced Trading Webhook provides:
- ✅ **Automatic position sizing** based on your risk tolerance
- ✅ **Smart position management** to prevent conflicts
- ✅ **Flexible trading actions** for any strategy
- ✅ **Comprehensive error handling** with helpful suggestions
- ✅ **Production-ready** with extensive logging and validation

Perfect for automated trading strategies that need precise control over position sizing and risk management!
