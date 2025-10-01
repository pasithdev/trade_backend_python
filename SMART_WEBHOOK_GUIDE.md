# Smart Webhook Documentation

## Overview
The Smart Webhook is a new endpoint that allows you to configure quantity percentage and leverage with intelligent defaults. It automatically converts percentage values to real quantities for any specific symbol.

## Endpoints
- **Primary**: `/api/binance/smart-webhook`
- **Alternative**: `/api/tradingview/binance/smart-webhook`
- **Test**: `/api/binance/test-smart-webhook`

## Default Values
- **Quantity Percentage**: 20% of available balance
- **Leverage**: 10x
- **Stop Loss**: 1.0%
- **Take Profit**: 2.0%

## Supported Actions
- `buy` or `long` - Opens a long position
- `sell` or `short` - Opens a short position  
- `close` - Closes all positions for the symbol

## Request Format

### Minimal Request (Uses Defaults)
```json
{
    "action": "buy",
    "symbol": "BTCUSDT"
}
```

### Full Request with Custom Settings
```json
{
    "action": "buy",
    "symbol": "ETHUSDT",
    "quantity_percent": 0.30,
    "leverage": 15,
    "entry": "3500.50",
    "sl_percent": 1.5,
    "tp_percent": 3.0
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | **required** | `buy`, `sell`, `long`, `short`, or `close` |
| `symbol` | string | **required** | Trading pair (e.g., `BTCUSDT`) |
| `quantity_percent` | float | 0.20 | Percentage of balance to use (0.01 = 1%, 1.0 = 100%) |
| `leverage` | integer | 10 | Leverage multiplier (1-125) |
| `entry` | float | optional | Entry price (for reference) |
| `sl_percent` | float | 1.0 | Stop loss percentage |
| `tp_percent` | float | 2.0 | Take profit percentage |

## Response Format

### Success Response
```json
{
    "success": true,
    "message": "Smart webhook order executed: buy 0.005 ETHUSDT",
    "trade": {
        "symbol": "ETHUSDT",
        "action": "buy",
        "quantity": 0.005,
        "quantity_percent": 0.20,
        "quantity_percent_display": "20%",
        "leverage": 10,
        "entry_price": 3500.50,
        "current_price": 3501.23,
        "estimated_fill_price": 3501.23,
        "main_order_id": 123456789,
        "opposite_position_closed": "No opposite positions",
        "stop_loss": {
            "enabled": true,
            "percent": 1.5,
            "price": 3448.71
        },
        "take_profit": {
            "enabled": true,
            "percent": 3.0,
            "price": 3606.27
        },
        "mode": "smart_webhook",
        "note": "Quantity: 20% of balance converted to 0.005 ETHUSDT"
    },
    "calculation_details": {
        "total_balance": 100.50,
        "available_balance": 100.50,
        "balance_percentage": 0.20,
        "leverage": 10,
        "position_value_usdt": 201.00,
        "current_price": 3501.23,
        "raw_quantity": 0.0057412,
        "final_quantity": 0.005
    },
    "symbol_requirements": {
        "min_quantity": 0.001,
        "step_size": 0.001,
        "min_notional": 5
    },
    "timestamp": "2025-10-01T12:34:56.789"
}
```

### Error Response
```json
{
    "success": false,
    "error": "Failed to calculate position quantity: Calculated quantity 0.0000028 is below minimum 0.001 for BTCUSDT. Need at least 36.15 USDT available balance (or 36.2% of current balance) to trade this symbol with 10x leverage.",
    "suggestions": [
        "Try using quantity_percent: 0.362 (minimum 36.2%)"
    ],
    "details": {
        "calculated_quantity": 0.0000028,
        "minimum_quantity": 0.001,
        "minimum_balance_needed": 36.15,
        "minimum_balance_percentage": 0.362,
        "position_value_usdt": 3.22,
        "current_price": 67500.0,
        "suggestion": "Increase balance_percentage to at least 0.362 or use a different symbol with lower minimum quantity"
    }
}
```

## Features

1. **Auto Quantity Conversion**: Converts percentage to real quantity based on:
   - Available account balance
   - Current symbol price
   - Leverage multiplier
   - Symbol precision requirements

2. **Intelligent Validation**:
   - Checks minimum quantity requirements
   - Validates symbol exists and is tradeable
   - Ensures sufficient balance
   - Provides specific error messages and suggestions

3. **Position Management**:
   - Automatically closes opposite positions
   - Sets leverage and margin type
   - Tracks all orders

4. **Flexible Input**:
   - Uses defaults when parameters are omitted
   - Supports both `buy`/`sell` and `long`/`short` syntax
   - Handles different content types from TradingView

## TradingView Integration

### Pine Script Alert Messages

#### Basic Buy Alert
```
{"action": "buy", "symbol": "{{ticker}}", "entry": "{{close}}"}
```

#### Custom Settings Alert
```
{"action": "sell", "symbol": "{{ticker}}", "quantity_percent": 0.25, "leverage": 12, "entry": "{{close}}"}
```

#### With Stop Loss and Take Profit
```
{"action": "long", "symbol": "{{ticker}}", "quantity_percent": 0.15, "leverage": 8, "sl_percent": 2.0, "tp_percent": 4.0, "entry": "{{close}}"}
```

#### Close Position Alert
```
{"action": "close", "symbol": "{{ticker}}"}
```

## Testing

Run the test script to verify functionality:

```bash
python test_smart_webhook.py
```

The test script will:
1. Test different scenarios (buy, sell, long, close)
2. Test quantity calculations for various symbols
3. Show detailed responses and error handling
4. Connect to server on port 80

## Error Handling

The webhook provides detailed error messages for common issues:

- **Insufficient Balance**: Shows exactly how much balance is needed
- **Invalid Quantity**: Explains minimum quantity requirements
- **Symbol Issues**: Validates symbol exists and is tradeable
- **API Errors**: Provides specific Binance error codes and suggestions

## Common Minimum Quantities

| Symbol | Min Quantity | Approx Min Balance (10x leverage) |
|--------|-------------|----------------------------------|
| BTCUSDT | 0.001 | ~$6.75 |
| ETHUSDT | 0.001 | ~$0.35 |
| ADAUSDT | 1.0 | ~$0.05 |
| DOGEUSDT | 1.0 | ~$0.01 |

## Best Practices

1. **Start Small**: Use 5-10% quantity for testing
2. **Check Balance**: Ensure sufficient balance for minimum quantities
3. **Use Appropriate Symbols**: Start with lower-priced coins (ADA, DOGE) for testing
4. **Monitor Logs**: Check server logs for detailed error information
5. **Test First**: Use the test endpoint before going live

## Comparison with Original Webhook

| Feature | Original Webhook | Smart Webhook |
|---------|-----------------|---------------|
| Default Quantity | Variable | 20% (configurable) |
| Default Leverage | Variable | 10x (configurable) |
| Error Messages | Basic | Detailed with suggestions |
| Quantity Validation | Limited | Comprehensive |
| Symbol Support | Specific format | Flexible |
| Configuration | Fixed | Fully configurable |
| Testing | Limited | Comprehensive test suite |