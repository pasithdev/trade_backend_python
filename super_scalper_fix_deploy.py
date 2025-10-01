#!/usr/bin/env python3
"""
Super Scalper Fix Deployment Script
This script contains the fixed function code that needs to be deployed to the server
"""

# FIXED CODE FOR get_symbol_minimum_requirements function
FIXED_FUNCTION_CODE = '''
def get_symbol_minimum_requirements(symbol):
    """
    Get minimum requirements for a symbol with enhanced error handling
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
    
    Returns:
        dict: Minimum quantity, price, and other requirements
    """
    global binance_client
    
    try:
        # Get exchange information with error handling
        logger.info(f"Fetching symbol requirements for {symbol}")
        exchange_info = call_binance_api(binance_client.futures_exchange_info)
        
        # Find symbol info
        symbol_info = None
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break
        
        if not symbol_info:
            raise ValueError(f"Symbol {symbol} not found in exchange info")
        
        logger.info(f"Found symbol info for {symbol}, extracting filters...")
        
        # Extract filters with better error handling
        lot_size_filter = None
        price_filter = None
        min_notional_filter = None
        market_lot_size_filter = None
        
        for f in symbol_info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                lot_size_filter = f
            elif f['filterType'] == 'PRICE_FILTER':
                price_filter = f
            elif f['filterType'] == 'MIN_NOTIONAL':
                min_notional_filter = f
            elif f['filterType'] == 'MARKET_LOT_SIZE':
                market_lot_size_filter = f
        
        # Validate required filters
        if not lot_size_filter:
            raise ValueError(f"LOT_SIZE filter not found for {symbol}")
        if not price_filter:
            raise ValueError(f"PRICE_FILTER not found for {symbol}")
        
        # Handle minimum notional - try different approaches
        min_notional = 0
        if min_notional_filter:
            try:
                # First try 'minNotional' field
                if 'minNotional' in min_notional_filter:
                    min_notional = float(min_notional_filter['minNotional'])
                # Then try 'notional' field
                elif 'notional' in min_notional_filter:
                    min_notional = float(min_notional_filter['notional'])
                # Handle other possible field names
                elif 'minNotionalValue' in min_notional_filter:
                    min_notional = float(min_notional_filter['minNotionalValue'])
                else:
                    logger.warning(f"MIN_NOTIONAL filter found but no recognizable field for {symbol}: {min_notional_filter}")
                    min_notional = 5.0  # Default minimum for futures
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error parsing MIN_NOTIONAL for {symbol}: {e}, using default")
                min_notional = 5.0
        else:
            logger.info(f"No MIN_NOTIONAL filter found for {symbol}, using default minimum")
            min_notional = 5.0  # Default minimum for futures trading
        
        logger.info(f"Successfully extracted requirements for {symbol}: min_qty={lot_size_filter['minQty']}, min_notional={min_notional}")
        
        return {
            'success': True,
            'min_qty': float(lot_size_filter['minQty']),
            'max_qty': float(lot_size_filter['maxQty']),
            'step_size': float(lot_size_filter['stepSize']),
            'min_price': float(price_filter['minPrice']),
            'max_price': float(price_filter['maxPrice']),
            'tick_size': float(price_filter['tickSize']),
            'min_notional': min_notional,
            'symbol_info': symbol_info,
            'filters': symbol_info['filters']  # Include all filters for debugging
        }
    except Exception as e:
        error_msg = f"Failed to get symbol requirements for {symbol}: {e}"
        logger.error(error_msg)
        logger.error(f"Exception type: {type(e).__name__}")
        
        # Try to provide fallback values for common symbols
        fallback_requirements = get_fallback_symbol_requirements(symbol)
        if fallback_requirements:
            logger.warning(f"Using fallback requirements for {symbol}")
            return fallback_requirements
        
        return {
            'success': False,
            'error': error_msg
        }

def get_fallback_symbol_requirements(symbol):
    """
    Provide fallback symbol requirements for common trading pairs
    when API calls fail
    """
    fallback_data = {
        'BTCUSDT': {'min_qty': 0.001, 'min_notional': 5.0, 'step_size': 0.001, 'tick_size': 0.01},
        'ETHUSDT': {'min_qty': 0.001, 'min_notional': 5.0, 'step_size': 0.001, 'tick_size': 0.01},
        'BNBUSDT': {'min_qty': 0.001, 'min_notional': 5.0, 'step_size': 0.001, 'tick_size': 0.01},
        'ADAUSDT': {'min_qty': 1.0, 'min_notional': 5.0, 'step_size': 1.0, 'tick_size': 0.0001},
        'DOGEUSDT': {'min_qty': 1.0, 'min_notional': 5.0, 'step_size': 1.0, 'tick_size': 0.000001},
        'XRPUSDT': {'min_qty': 0.1, 'min_notional': 5.0, 'step_size': 0.1, 'tick_size': 0.0001},
        'SOLUSDT': {'min_qty': 0.001, 'min_notional': 5.0, 'step_size': 0.001, 'tick_size': 0.001},
        'DOTUSDT': {'min_qty': 0.01, 'min_notional': 5.0, 'step_size': 0.01, 'tick_size': 0.001},
        'LINKUSDT': {'min_qty': 0.01, 'min_notional': 5.0, 'step_size': 0.01, 'tick_size': 0.001},
        'LTCUSDT': {'min_qty': 0.001, 'min_notional': 5.0, 'step_size': 0.001, 'tick_size': 0.01}
    }
    
    if symbol in fallback_data:
        data = fallback_data[symbol]
        logger.info(f"Using fallback requirements for {symbol}: {data}")
        return {
            'success': True,
            'min_qty': data['min_qty'],
            'max_qty': 9000000000.0,  # Large default
            'step_size': data['step_size'],
            'min_price': 0.000001,  # Small default
            'max_price': 1000000.0,  # Large default
            'tick_size': data['tick_size'],
            'min_notional': data['min_notional'],
            'fallback': True,
            'symbol_info': None
        }
    
    return None
'''

# Manual deployment instructions
DEPLOYMENT_INSTRUCTIONS = """
🚨 SUPER SCALPER WEBHOOK FIX DEPLOYMENT 🚨

TO APPLY THIS FIX TO YOUR SERVER (167.71.207.209):

1. SSH to your server:
   ssh root@167.71.207.209

2. Navigate to your app directory:
   cd /path/to/your/app

3. Backup the current file:
   cp src/routes/binance_trading.py src/routes/binance_trading.py.backup

4. Edit the file:
   nano src/routes/binance_trading.py

5. Find the function 'get_symbol_minimum_requirements' (around line 1130)

6. Replace the ENTIRE function with the fixed code from this file

7. Add the new fallback function after it

8. Save the file (Ctrl+X, Y, Enter)

9. Restart the application:
   pkill -f main.py
   sleep 3
   nohup python src/main.py > trading_system.log 2>&1 &

10. Reconfigure API:
    curl -X POST http://localhost/api/binance/config -H "Content-Type: application/json" -d '{"api_key": "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ", "api_secret": "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF", "testnet": false}'

11. Test the fix:
    curl -X POST http://localhost/api/binance/super-scalper-webhook -H "Content-Type: application/json" -d '{"symbol": "ETHUSDT", "action": "buy", "balance_percentage": 0.50, "leverage": 10, "entry": 2456.78}'

EXPECTED RESULT: Should return success instead of "Failed to get symbol requirements" error!
"""

def main():
    print("=" * 80)
    print("SUPER SCALPER WEBHOOK FIX")
    print("=" * 80)
    print()
    print("This script contains the fixed code for the Super Scalper webhook issue.")
    print("The fixed function handles the 'minNotional' field error robustly.")
    print()
    print("WHAT'S FIXED:")
    print("- Enhanced error handling for missing API fields")
    print("- Multiple field name attempts (minNotional, notional, minNotionalValue)")
    print("- Fallback symbol requirements for common trading pairs")
    print("- Detailed logging for debugging")
    print("- Default minimum values when API calls fail")
    print()
    print(DEPLOYMENT_INSTRUCTIONS)
    print()
    print("=" * 80)
    print("FIXED FUNCTION CODE ABOVE ☝️")
    print("Copy this entire function to your server's binance_trading.py file")
    print("=" * 80)

if __name__ == "__main__":
    main()
    print(FIXED_FUNCTION_CODE)