from flask import Blueprint, request, jsonify
import os
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
import logging
from datetime import datetime
import json

binance_bp = Blueprint('binance', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔒 PERMANENT BINANCE API CREDENTIALS
# These credentials are stored permanently to prevent API configuration loss
PERMANENT_API_CREDENTIALS = {
    'api_key': 'M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ',
    'api_secret': 'bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF',
    'testnet': False  # Production mode
}

# Global variables for Binance client and configuration
binance_client = None
trading_config = {
    'testnet': False,  # Production mode with permanent credentials
    'default_tp_percentage': 2.0,  # 2% take profit
    'default_sl_percentage': 1.0,  # 1% stop loss
    'default_quantity_percentage': 0.20,  # 20% of balance (new default)
    'default_leverage': 10,  # 10x leverage (new default)
    'min_order_value': 10.0,  # Minimum order value in USDT
    'max_order_value': 1000.0,  # Maximum order value in USDT
    'leverage': 10,  # Default leverage for futures trading
    'margin_type': 'ISOLATED',  # ISOLATED or CROSSED
    'position_side': 'BOTH'  # BOTH, LONG, or SHORT (for hedge mode)
}

# Store active orders for tracking
active_orders = []

def auto_init_binance_client():
    """
    Automatically initialize Binance client using permanent credentials
    This prevents API configuration loss issues
    """
    global binance_client
    
    if binance_client is not None:
        logger.info("Binance client already initialized")
        return True
    
    try:
        logger.info("Auto-initializing Binance client with permanent credentials...")
        success = init_binance_client(
            PERMANENT_API_CREDENTIALS['api_key'],
            PERMANENT_API_CREDENTIALS['api_secret'],
            PERMANENT_API_CREDENTIALS['testnet']
        )
        
        if success:
            logger.info("✅ Binance client auto-initialized successfully with permanent credentials")
            return True
        else:
            logger.error("❌ Failed to auto-initialize Binance client")
            return False
            
    except Exception as e:
        logger.error(f"❌ Auto-initialization error: {e}")
        return False

def ensure_binance_client():
    """
    Ensure Binance client is initialized, auto-initialize if needed
    Call this before any Binance API operations
    """
    global binance_client
    
    if binance_client is None:
        logger.info("Binance client not initialized, auto-initializing...")
        return auto_init_binance_client()
    
    return True

def log_binance_api_call(method_name, params=None, response=None, error=None):
    """
    Log Binance API calls with request parameters and response data
    """
    try:
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'api_method': method_name,
            'request_params': params if params else {},
            'success': error is None
        }
        
        if error:
            log_data['error'] = str(error)
            logger.error(f"BINANCE API ERROR - {method_name}: {json.dumps(log_data, indent=2, default=str)}")
        else:
            # Only log response for successful calls, and limit size to prevent log spam
            if response is not None:
                if isinstance(response, (list, dict)):
                    # Truncate large responses
                    if isinstance(response, list) and len(response) > 10:
                        log_data['response'] = response[:10] + [f"... and {len(response)-10} more items"]
                    elif isinstance(response, dict) and len(str(response)) > 2000:
                        log_data['response'] = f"Large response ({len(str(response))} chars): {str(response)[:500]}..."
                    else:
                        log_data['response'] = response
                else:
                    log_data['response'] = response
            
            logger.info(f"BINANCE API CALL - {method_name}: {json.dumps(log_data, indent=2, default=str)}")
            
    except Exception as log_error:
        logger.error(f"Error logging Binance API call: {log_error}")

def call_binance_api(api_method, *args, **kwargs):
    """
    Wrapper function to call Binance API methods with logging
    """
    method_name = api_method.__name__ if hasattr(api_method, '__name__') else str(api_method)
    
    # Prepare parameters for logging
    params = {}
    if args:
        params['args'] = args
    if kwargs:
        params['kwargs'] = kwargs
    
    try:
        # Make the API call
        response = api_method(*args, **kwargs)
        
        # Log successful call
        log_binance_api_call(method_name, params, response)
        
        return response
        
    except (BinanceAPIException, BinanceOrderException) as e:
        # Log API error
        log_binance_api_call(method_name, params, error=e)
        raise
    except Exception as e:
        # Log unexpected error
        log_binance_api_call(method_name, params, error=e)
        raise

def init_binance_client(api_key, api_secret, testnet=True):
    """Initialize Binance client with API credentials for Futures trading"""
    global binance_client
    try:
        import asyncio
        import threading
        
        logger.info(f"Initializing Binance client (testnet: {testnet})")
        
        # Fix event loop issue for Flask threading
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # Create new event loop if none exists or if closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Created new asyncio event loop for thread")
        
        if testnet:
            # For testnet, we need to specify the testnet base URL
            binance_client = Client(
                api_key, 
                api_secret, 
                testnet=True,
                tld='com'  # Ensure we're using binance.com testnet
            )
            logger.info("Created testnet Binance client")
        else:
            binance_client = Client(api_key, api_secret)
            logger.info("Created mainnet Binance client")
        
        # Test basic connection first
        try:
            server_time = call_binance_api(binance_client.get_server_time)
            logger.info(f"Server time test successful: {server_time}")
        except Exception as server_error:
            logger.error(f"Failed to get server time: {server_error}")
            raise Exception(f"Basic connection test failed: {server_error}")
        
        # Test the futures connection
        try:
            futures_account_info = call_binance_api(binance_client.futures_account)
            logger.info(f"Binance Futures client initialized successfully. Total Wallet Balance: {futures_account_info.get('totalWalletBalance', 'Unknown')}")
        except Exception as futures_error:
            logger.error(f"Futures account access failed: {futures_error}")
            # If it's a testnet, provide specific guidance
            if testnet:
                raise Exception(f"Futures testnet access failed: {futures_error}. Make sure you're using Binance Futures Testnet API keys from https://testnet.binancefuture.com/")
            else:
                raise Exception(f"Futures account access failed: {futures_error}. Make sure your API key has futures trading permissions.")
        
        # Set position mode to One-way (BOTH) by default
        try:
            call_binance_api(binance_client.futures_change_position_mode, dualSidePosition=False)
            logger.info("Position mode set to One-way (BOTH)")
        except Exception as pos_error:
            logger.warning(f"Could not set position mode (may already be set): {pos_error}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Binance Futures client: {str(e)}")
        binance_client = None
        return False

@binance_bp.route('/binance/config', methods=['POST'])
def configure_binance():
    """Configure Binance API credentials and trading settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing configuration data'
            }), 400
        
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        testnet = data.get('testnet', True)
        
        if not api_key or not api_secret:
            return jsonify({
                'success': False,
                'error': 'API key and secret are required'
            }), 400
        
        # Update trading configuration
        if 'tp_percentage' in data:
            trading_config['default_tp_percentage'] = float(data['tp_percentage'])
        if 'sl_percentage' in data:
            trading_config['default_sl_percentage'] = float(data['sl_percentage'])
        if 'min_order_value' in data:
            trading_config['min_order_value'] = float(data['min_order_value'])
        if 'max_order_value' in data:
            trading_config['max_order_value'] = float(data['max_order_value'])
        if 'leverage' in data:
            leverage = int(data['leverage'])
            if leverage < 1 or leverage > 125:
                return jsonify({
                    'success': False,
                    'error': 'Leverage must be between 1 and 125'
                }), 400
            trading_config['leverage'] = leverage
        if 'margin_type' in data:
            margin_type = data['margin_type'].upper()
            if margin_type not in ['ISOLATED', 'CROSSED']:
                return jsonify({
                    'success': False,
                    'error': 'Margin type must be ISOLATED or CROSSED'
                }), 400
            trading_config['margin_type'] = margin_type
        
        trading_config['testnet'] = testnet
        
        # Initialize Binance client
        try:
            success = init_binance_client(api_key, api_secret, testnet)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Binance Futures configuration updated successfully',
                    'config': {
                        'testnet': trading_config['testnet'],
                        'tp_percentage': trading_config['default_tp_percentage'],
                        'sl_percentage': trading_config['default_sl_percentage'],
                        'min_order_value': trading_config['min_order_value'],
                        'max_order_value': trading_config['max_order_value'],
                        'leverage': trading_config['leverage'],
                        'margin_type': trading_config['margin_type'],
                        'position_side': trading_config['position_side']
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to initialize Binance client - check server logs for detailed error information'
                }), 400
        except Exception as init_error:
            logger.error(f"Configuration initialization error: {str(init_error)}")
            return jsonify({
                'success': False,
                'error': f'Configuration failed: {str(init_error)}'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }), 500

@binance_bp.route('/binance/validate-credentials', methods=['POST'])
def validate_credentials():
    """Validate Binance API credentials without saving configuration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing credential data'
            }), 400
        
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        testnet = data.get('testnet', True)
        
        if not api_key or not api_secret:
            return jsonify({
                'success': False,
                'error': 'API key and secret are required'
            }), 400
        
        # Test without saving to global config
        try:
            logger.info(f"Testing credentials (testnet: {testnet})")
            
            if testnet:
                test_client = Client(api_key, api_secret, testnet=True, tld='com')
            else:
                test_client = Client(api_key, api_secret)
            
            # Test basic connection
            server_time = test_client.get_server_time()
            logger.info("Server time test passed")
            
            # Test futures account access
            futures_account = test_client.futures_account()
            logger.info("Futures account access test passed")
            
            return jsonify({
                'success': True,
                'message': 'API credentials are valid for futures trading',
                'details': {
                    'testnet': testnet,
                    'server_time': server_time,
                    'can_trade': futures_account.get('canTrade', False),
                    'total_wallet_balance': futures_account.get('totalWalletBalance', '0'),
                    'account_alias': futures_account.get('accountAlias', 'Unknown')
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as test_error:
            error_msg = str(test_error)
            suggestions = []
            
            if 'Invalid API-key' in error_msg:
                suggestions.append("Check that your API key is correct")
                suggestions.append("Make sure you're using the right testnet/mainnet API key")
            elif 'Invalid signature' in error_msg:
                suggestions.append("Check that your API secret is correct")
                suggestions.append("Make sure there are no extra spaces in your API secret")
            elif 'IP' in error_msg:
                suggestions.append("Check your IP whitelist settings in Binance")
                suggestions.append("Make sure your IP is allowed to access the API")
            elif 'Permission' in error_msg:
                suggestions.append("Enable Futures Trading permissions for your API key")
                suggestions.append("Check API key restrictions in your Binance account")
            elif 'testnet' in error_msg.lower():
                suggestions.append("Make sure you're using Binance Futures Testnet API keys")
                suggestions.append("Get testnet API keys from: https://testnet.binancefuture.com/")
            
            return jsonify({
                'success': False,
                'error': f'API validation failed: {error_msg}',
                'suggestions': suggestions,
                'testnet_info': {
                    'message': 'For testnet, you need API keys from https://testnet.binancefuture.com/',
                    'note': 'Testnet API keys are different from mainnet API keys'
                } if testnet else None
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 500

@binance_bp.route('/binance/account', methods=['GET'])
def get_account_info():
    """Get Binance Futures account information"""
    global binance_client
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured. Please configure API credentials first.'
        }), 400
    
    try:
        # Get futures account information
        futures_account = call_binance_api(binance_client.futures_account)
        
        # Get positions
        positions = call_binance_api(binance_client.futures_position_information)
        
        # Filter positions with size > 0
        active_positions = [
            {
                'symbol': pos['symbol'],
                'position_amt': float(pos['positionAmt']),
                'entry_price': float(pos['entryPrice']),
                'mark_price': float(pos['markPrice']),
                'pnl': float(pos['unRealizedProfit']),
                'percentage': float(pos['percentage']),
                'position_side': pos['positionSide']
            }
            for pos in positions
            if float(pos['positionAmt']) != 0
        ]
        
        # Extract relevant account information
        account_data = {
            'total_wallet_balance': float(futures_account.get('totalWalletBalance', 0)),
            'total_unrealized_profit': float(futures_account.get('totalUnrealizedProfit', 0)),
            'total_margin_balance': float(futures_account.get('totalMarginBalance', 0)),
            'total_position_initial_margin': float(futures_account.get('totalPositionInitialMargin', 0)),
            'total_open_order_initial_margin': float(futures_account.get('totalOpenOrderInitialMargin', 0)),
            'available_balance': float(futures_account.get('availableBalance', 0)),
            'max_withdraw_amount': float(futures_account.get('maxWithdrawAmount', 0)),
            'can_trade': futures_account.get('canTrade', False),
            'can_deposit': futures_account.get('canDeposit', False),
            'can_withdraw': futures_account.get('canWithdraw', False),
            'active_positions': active_positions,
            'assets': [
                {
                    'asset': asset['asset'],
                    'wallet_balance': float(asset['walletBalance']),
                    'unrealized_profit': float(asset['unrealizedProfit']),
                    'margin_balance': float(asset['marginBalance']),
                    'available_balance': float(asset['availableBalance'])
                }
                for asset in futures_account.get('assets', [])
                if float(asset['walletBalance']) > 0
            ]
        }
        
        return jsonify({
            'success': True,
            'account': account_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching futures account info: {str(e)}'
        }), 500

@binance_bp.route('/binance/trade', methods=['POST'])
def execute_trade():
    """Execute a trade based on TradingView signal with TP/SL"""
    global binance_client, active_orders
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured. Please configure API credentials first.'
        }), 400
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing trade data'
            }), 400
        
        # Extract trade parameters
        symbol = data.get('symbol', '').upper()
        action = data.get('action', '').lower()  # 'buy' or 'sell'
        quantity = data.get('quantity')
        order_value = data.get('order_value')  # in USDT
        tp_percentage = data.get('tp_percentage', trading_config['default_tp_percentage'])
        sl_percentage = data.get('sl_percentage', trading_config['default_sl_percentage'])
        
        if not symbol or action not in ['buy', 'sell']:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol or action. Action must be "buy" or "sell"'
            }), 400
        
        # Ensure symbol ends with USDT for spot trading
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        # Get current price
        ticker = call_binance_api(binance_client.get_symbol_ticker, symbol=symbol)
        current_price = float(ticker['price'])
        
        # Calculate quantity if order_value is provided
        if order_value and not quantity:
            if order_value < trading_config['min_order_value'] or order_value > trading_config['max_order_value']:
                return jsonify({
                    'success': False,
                    'error': f'Order value must be between {trading_config["min_order_value"]} and {trading_config["max_order_value"]} USDT'
                }), 400
            quantity = order_value / current_price
        
        if not quantity:
            return jsonify({
                'success': False,
                'error': 'Either quantity or order_value must be provided'
            }), 400
        
        # Round quantity to appropriate precision
        symbol_info = call_binance_api(binance_client.get_symbol_info, symbol)
        lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size_filter['stepSize'])
        quantity = round(quantity - (quantity % step_size), 8)
        
        if action == 'buy':
            # Place market buy order
            order = call_binance_api(binance_client.order_market_buy,
                symbol=symbol,
                quantity=quantity
            )
            
            # Calculate TP and SL prices
            tp_price = current_price * (1 + tp_percentage / 100)
            sl_price = current_price * (1 - sl_percentage / 100)
            
            # Place OCO sell order for TP/SL
            oco_order = call_binance_api(binance_client.create_oco_order,
                symbol=symbol,
                side=SIDE_SELL,
                quantity=quantity,
                price=f"{tp_price:.8f}",  # Take profit price
                stopPrice=f"{sl_price:.8f}",  # Stop loss trigger price
                stopLimitPrice=f"{sl_price * 0.99:.8f}",  # Stop loss limit price (slightly lower)
                stopLimitTimeInForce=TIME_IN_FORCE_GTC
            )
            
        else:  # sell
            # For sell orders, we assume user already has the asset
            # Place market sell order
            order = call_binance_api(binance_client.order_market_sell,
                symbol=symbol,
                quantity=quantity
            )
            
            # For sell orders, TP is lower price, SL is higher price
            tp_price = current_price * (1 - tp_percentage / 100)
            sl_price = current_price * (1 + sl_percentage / 100)
            
            # Place OCO buy order for TP/SL
            oco_order = call_binance_api(binance_client.create_oco_order,
                symbol=symbol,
                side=SIDE_BUY,
                quantity=quantity,
                price=f"{tp_price:.8f}",  # Take profit price
                stopPrice=f"{sl_price:.8f}",  # Stop loss trigger price
                stopLimitPrice=f"{sl_price * 1.01:.8f}",  # Stop loss limit price (slightly higher)
                stopLimitTimeInForce=TIME_IN_FORCE_GTC
            )
        
        # Store order information
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'current_price': current_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'tp_percentage': tp_percentage,
            'sl_percentage': sl_percentage,
            'main_order': order,
            'oco_order': oco_order,
            'status': 'active'
        }
        
        active_orders.append(trade_record)
        
        logger.info(f"Trade executed: {action} {quantity} {symbol} at {current_price}")
        
        return jsonify({
            'success': True,
            'message': f'Trade executed successfully: {action} {quantity} {symbol}',
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'execution_price': current_price,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'main_order_id': order['orderId'],
                'oco_order_id': oco_order['orderListId']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        logger.error(f"Binance API error: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except BinanceOrderException as e:
        logger.error(f"Binance order error: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Order error: {e.message}'
        }), 400
    except Exception as e:
        logger.error(f"Trade execution error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Trade execution error: {str(e)}'
        }), 500

@binance_bp.route('/binance/orders', methods=['GET'])
def get_active_orders():
    """Get all active orders"""
    global active_orders
    
    return jsonify({
        'success': True,
        'orders': active_orders,
        'count': len(active_orders),
        'timestamp': datetime.now().isoformat()
    })

@binance_bp.route('/binance/orders/<symbol>', methods=['GET'])
def get_orders_by_symbol(symbol):
    """Get futures orders for a specific symbol"""
    global binance_client
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured'
        }), 400
    
    try:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        # Get open futures orders
        orders = call_binance_api(binance_client.futures_get_open_orders, symbol=symbol)
        
        # Get position information
        positions = call_binance_api(binance_client.futures_position_information, symbol=symbol)
        position_info = [pos for pos in positions if float(pos['positionAmt']) != 0]
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'open_orders': orders,
            'positions': position_info,
            'order_count': len(orders),
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching futures orders: {str(e)}'
        }), 500

def execute_tradingview_trade(alert_data):
    """
    Execute trade based on TradingView alert data with TP/SL prices
    This function is called internally from TradingView webhook
    """
    global binance_client, active_orders
    
    if not binance_client:
        logger.error("Binance client not configured for TradingView trade")
        return {
            'success': False,
            'error': 'Binance client not configured. Please configure API credentials first.',
            'trade_executed': False
        }
    
    try:
        # Extract trade parameters from alert
        symbol = alert_data.get('symbol', '').upper()
        action = alert_data.get('action', '').lower()
        entry_price = alert_data.get('price')
        tp_price = alert_data.get('tp')
        sl_price = alert_data.get('sl')
        quantity = alert_data.get('quantity')
        
        # Validate required parameters
        if not symbol or action not in ['buy', 'sell']:
            return {
                'success': False,
                'error': 'Invalid symbol or action in TradingView alert',
                'trade_executed': False
            }
        
        # Convert symbol format (BTCUSD -> BTCUSDT)
        if symbol.endswith('USD') and not symbol.endswith('USDT'):
            symbol = symbol.replace('USD', 'USDT')
        elif not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        # Get current market price from futures
        ticker = call_binance_api(binance_client.futures_symbol_ticker, symbol=symbol)
        current_price = float(ticker['price'])
        
        # Set leverage for the symbol
        try:
            call_binance_api(binance_client.futures_change_leverage, symbol=symbol, leverage=trading_config['leverage'])
            logger.info(f"Leverage set to {trading_config['leverage']}x for {symbol}")
        except Exception as lev_error:
            logger.warning(f"Could not set leverage for {symbol}: {lev_error}")
        
        # Set margin type
        try:
            call_binance_api(binance_client.futures_change_margin_type, symbol=symbol, marginType=trading_config['margin_type'])
            logger.info(f"Margin type set to {trading_config['margin_type']} for {symbol}")
        except Exception as margin_error:
            logger.warning(f"Could not set margin type for {symbol} (may already be set): {margin_error}")
        
        # Calculate quantity if not provided
        if not quantity:
            # Use default order value for automatic trades
            order_value = trading_config['min_order_value'] * 2
            quantity = order_value / current_price
        else:
            quantity = float(quantity)
        
        # Get futures symbol precision info
        exchange_info = call_binance_api(binance_client.futures_exchange_info)
        symbol_info = next(s for s in exchange_info['symbols'] if s['symbol'] == symbol)
        
        lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
        
        step_size = float(lot_size_filter['stepSize'])
        tick_size = float(price_filter['tickSize'])
        
        # Round quantity to appropriate precision
        quantity = round(quantity - (quantity % step_size), 8)
        
        if quantity <= 0:
            return {
                'success': False,
                'error': 'Calculated quantity is too small',
                'trade_executed': False
            }
        
        # Execute main futures order
        side = 'BUY' if action == 'buy' else 'SELL'
        
        # Generate unique client order ID for better tracking
        import uuid
        client_order_id = f"TV_{action}_{symbol}_{int(datetime.now().timestamp())}"
        
        main_order = call_binance_api(binance_client.futures_create_order,
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity,
            newClientOrderId=client_order_id
        )
        
        logger.info(f"Main order executed: {action} {quantity} {symbol} (Client ID: {client_order_id})")
        
        # Handle TP/SL orders if prices are provided (using futures-specific orders)
        tp_order = None
        sl_order = None
        final_tp_price = None
        final_sl_price = None
        
        if tp_price or sl_price:
            # Determine position side for closing orders
            if action == 'buy':
                # For buy (long) positions, we sell to close
                close_side = 'SELL'
                
                if tp_price:
                    final_tp_price = float(tp_price)
                    final_tp_price = round(final_tp_price - (final_tp_price % tick_size), 8)
                else:
                    # Fallback to calculated TP if not provided
                    final_tp_price = current_price * (1 + trading_config['default_tp_percentage'] / 100)
                    final_tp_price = round(final_tp_price - (final_tp_price % tick_size), 8)
                
                if sl_price:
                    final_sl_price = float(sl_price)
                    final_sl_price = round(final_sl_price - (final_sl_price % tick_size), 8)
                else:
                    # Fallback to calculated SL if not provided
                    final_sl_price = current_price * (1 - trading_config['default_sl_percentage'] / 100)
                    final_sl_price = round(final_sl_price - (final_sl_price % tick_size), 8)
                
            else:  # sell order
                # For sell (short) positions, we buy to close
                close_side = 'BUY'
                
                if tp_price:
                    final_tp_price = float(tp_price)
                    final_tp_price = round(final_tp_price - (final_tp_price % tick_size), 8)
                else:
                    # Fallback to calculated TP if not provided
                    final_tp_price = current_price * (1 - trading_config['default_tp_percentage'] / 100)
                    final_tp_price = round(final_tp_price - (final_tp_price % tick_size), 8)
                
                if sl_price:
                    final_sl_price = float(sl_price)
                    final_sl_price = round(final_sl_price - (final_sl_price % tick_size), 8)
                else:
                    # Fallback to calculated SL if not provided
                    final_sl_price = current_price * (1 + trading_config['default_sl_percentage'] / 100)
                    final_sl_price = round(final_sl_price - (final_sl_price % tick_size), 8)
            
            # Log the TP/SL prices being used
            logger.info(f"Using TradingView prices - TP: {final_tp_price}, SL: {final_sl_price}, Current: {current_price}")
            
            # Place Take Profit order
            if final_tp_price:
                try:
                    tp_client_order_id = f"TP_{action}_{symbol}_{int(datetime.now().timestamp())}"
                    tp_order = call_binance_api(binance_client.futures_create_order,
                        symbol=symbol,
                        side=close_side,
                        type='TAKE_PROFIT_MARKET',
                        quantity=quantity,
                        stopPrice=final_tp_price,
                        reduceOnly=True,
                        timeInForce='GTC',
                        workingType='CONTRACT_PRICE',
                        newClientOrderId=tp_client_order_id
                    )
                    logger.info(f"Take Profit order placed: {close_side} {quantity} at {final_tp_price} (Client ID: {tp_client_order_id})")
                except Exception as tp_error:
                    logger.error(f"Failed to place Take Profit order: {str(tp_error)}")
            
            # Place Stop Loss order
            if final_sl_price:
                try:
                    sl_client_order_id = f"SL_{action}_{symbol}_{int(datetime.now().timestamp())}"
                    sl_order = call_binance_api(binance_client.futures_create_order,
                        symbol=symbol,
                        side=close_side,
                        type='STOP_MARKET',
                        quantity=quantity,
                        stopPrice=final_sl_price,
                        reduceOnly=True,
                        timeInForce='GTC',
                        workingType='CONTRACT_PRICE',
                        newClientOrderId=sl_client_order_id
                    )
                    logger.info(f"Stop Loss order placed: {close_side} {quantity} at {final_sl_price} (Client ID: {sl_client_order_id})")
                except Exception as sl_error:
                    logger.error(f"Failed to place Stop Loss order: {str(sl_error)}")
        
        # Store trade record
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'source': 'tradingview_webhook',
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'entry_price': current_price,
            'tp_price': final_tp_price,
            'sl_price': final_sl_price,
            'leverage': trading_config['leverage'],
            'margin_type': trading_config['margin_type'],
            'main_order': main_order,
            'tp_order': tp_order,
            'sl_order': sl_order,
            'alert_data': alert_data,
            'status': 'active'
        }
        
        active_orders.append(trade_record)
        
        logger.info(f"TradingView trade executed successfully: {action} {quantity} {symbol} at {current_price}")
        
        return {
            'success': True,
            'message': f'TradingView futures trade executed: {action} {quantity} {symbol}',
            'trade_executed': True,
            'trade_details': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'execution_price': current_price,
                'tp_price': final_tp_price,
                'sl_price': final_sl_price,
                'leverage': trading_config['leverage'],
                'margin_type': trading_config['margin_type'],
                'main_order_id': main_order.get('orderId'),
                'tp_order_id': tp_order.get('orderId') if tp_order else None,
                'sl_order_id': sl_order.get('orderId') if sl_order else None
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except BinanceAPIException as e:
        logger.error(f"Binance API error in TradingView trade: {e.message}")
        return {
            'success': False,
            'error': f'Binance API error: {e.message}',
            'trade_executed': False
        }
    except BinanceOrderException as e:
        logger.error(f"Binance order error in TradingView trade: {e.message}")
        return {
            'success': False,
            'error': f'Order error: {e.message}',
            'trade_executed': False
        }
    except Exception as e:
        logger.error(f"Error executing TradingView trade: {str(e)}")
        return {
            'success': False,
            'error': f'Trade execution error: {str(e)}',
            'trade_executed': False
        }

@binance_bp.route('/binance/webhook-trade', methods=['POST'])
def webhook_trade():
    """Execute trade based on TradingView webhook signal"""
    try:
        # Get the webhook data (from TradingView)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No webhook data received'
            }), 400
        
        # Extract trading signal information
        symbol = data.get('symbol', '').replace('USD', 'USDT')  # Convert BTCUSD to BTCUSDT
        action = data.get('action', '').lower()
        price = data.get('price')
        
        if not symbol or action not in ['buy', 'sell']:
            return jsonify({
                'success': False,
                'error': 'Invalid webhook data: missing symbol or action'
            }), 400
        
        # Use default order value for webhook trades
        order_value = trading_config['min_order_value'] * 2  # Use 2x minimum order value
        
        # Execute the trade
        trade_data = {
            'symbol': symbol,
            'action': action,
            'order_value': order_value,
            'tp_percentage': trading_config['default_tp_percentage'],
            'sl_percentage': trading_config['default_sl_percentage']
        }
        
        # Call the execute_trade function internally
        with binance_bp.test_request_context('/binance/trade', method='POST', json=trade_data):
            response = execute_trade()
            
        return response
        
    except Exception as e:
        logger.error(f"Webhook trade error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Webhook trade error: {str(e)}'
        }), 500

def close_opposite_position_immediate(symbol, new_action):
    """
    IMMEDIATELY close any existing opposite position for the given symbol before opening new position
    Ensures immediate execution and confirmation before proceeding
    new_action: 'buy' for long, 'sell' for short
    """
    global binance_client
    
    if not binance_client:
        return {'success': False, 'error': 'Binance client not configured'}
    
    try:
        logger.info(f"🔄 IMMEDIATE CHECK: Looking for opposite positions to close for {symbol} before {new_action}")
        
        # Get current positions for the symbol
        positions = call_binance_api(binance_client.futures_position_information, symbol=symbol)
        positions_closed = []
        total_closed_value = 0
        
        for position in positions:
            position_amt = float(position['positionAmt'])
            
            # Skip if no position
            if position_amt == 0:
                continue
            
            # Determine if we need to close this position
            should_close = False
            close_side = None
            close_quantity = abs(position_amt)
            position_type = None
            
            if new_action == 'buy' and position_amt < 0:  # Closing short position before buy
                should_close = True
                close_side = 'BUY'
                position_type = 'SHORT'
                logger.info(f"⚠️  FOUND SHORT POSITION: {position_amt} {symbol} - MUST CLOSE IMMEDIATELY before BUY")
            elif new_action == 'sell' and position_amt > 0:  # Closing long position before sell
                should_close = True
                close_side = 'SELL' 
                position_type = 'LONG'
                logger.info(f"⚠️  FOUND LONG POSITION: {position_amt} {symbol} - MUST CLOSE IMMEDIATELY before SELL")
            
            if should_close:
                # Generate unique client order ID for closing order
                import uuid
                close_client_order_id = f"CLOSE_{position_type}_{symbol}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
                
                # IMMEDIATELY close the position with MARKET order
                logger.info(f"🚀 CLOSING {position_type} POSITION IMMEDIATELY: {close_side} {close_quantity} {symbol}")
                
                close_order = call_binance_api(binance_client.futures_create_order,
                    symbol=symbol,
                    side=close_side,
                    type='MARKET',
                    quantity=close_quantity,
                    reduceOnly=True,
                    newClientOrderId=close_client_order_id
                )
                
                # Calculate closed position value
                entry_price = float(position.get('entryPrice', 0))
                mark_price = float(position.get('markPrice', 0))
                closed_value = close_quantity * mark_price
                total_closed_value += closed_value
                
                positions_closed.append({
                    'position_type': position_type,
                    'side': close_side,
                    'quantity': close_quantity,
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'closed_value': closed_value,
                    'order_id': close_order['orderId'],
                    'client_order_id': close_client_order_id
                })
                
                logger.info(f"✅ {position_type} POSITION CLOSED: {close_side} {close_quantity} {symbol} at ~{mark_price} - Order ID: {close_order['orderId']}")
                
                # Cancel any existing TP/SL orders for this symbol to avoid conflicts
                try:
                    existing_orders = call_binance_api(binance_client.futures_get_open_orders, symbol=symbol)
                    cancelled_orders = []
                    for order in existing_orders:
                        call_binance_api(binance_client.futures_cancel_order, symbol=symbol, orderId=order['orderId'])
                        cancelled_orders.append(order['orderId'])
                        logger.info(f"🗑️  Cancelled existing order {order['orderId']} for {symbol}")
                    
                    if cancelled_orders:
                        logger.info(f"🧹 Cancelled {len(cancelled_orders)} existing orders for clean slate")
                        
                except Exception as cancel_error:
                    logger.warning(f"⚠️  Error cancelling existing orders for {symbol}: {cancel_error}")
        
        if positions_closed:
            return {
                'success': True, 
                'position_closed': True,
                'message': f'✅ IMMEDIATELY CLOSED {len(positions_closed)} opposite position(s) for {symbol} (Total value: {total_closed_value:.2f} USDT)',
                'closed_positions': positions_closed,
                'total_closed_value': total_closed_value,
                'ready_for_new_order': True
            }
        else:
            logger.info(f"✅ No opposite positions found for {symbol} - Ready to proceed with {new_action}")
            return {
                'success': True, 
                'position_closed': False,
                'message': 'No opposite positions to close - Ready for new order',
                'ready_for_new_order': True
            }
        
    except BinanceAPIException as e:
        logger.error(f"❌ Binance API error while closing opposite position: {e.message}")
        return {'success': False, 'error': f'Binance API error: {e.message}'}
    except Exception as e:
        logger.error(f"❌ Error closing opposite position: {str(e)}")
        return {'success': False, 'error': f'Error closing opposite position: {str(e)}'}

def close_opposite_position(symbol, new_action):
    """
    Close any existing opposite position for the given symbol before opening new position
    new_action: 'buy' for long, 'sell' for short
    """
    global binance_client
    
    if not binance_client:
        return {'success': False, 'error': 'Binance client not configured'}
    
    try:
        logger.info(f"Checking for opposite positions to close for {symbol} before {new_action}")
        
        # Get current positions for the symbol
        positions = call_binance_api(binance_client.futures_position_information, symbol=symbol)
        
        for position in positions:
            position_amt = float(position['positionAmt'])
            
            # Skip if no position
            if position_amt == 0:
                continue
            
            # Determine if we need to close this position
            should_close = False
            close_side = None
            close_quantity = abs(position_amt)
            
            if new_action == 'buy' and position_amt < 0:  # Closing short position before buy
                should_close = True
                close_side = 'BUY'
                logger.info(f"Found short position {position_amt} for {symbol}, will close before buy")
            elif new_action == 'sell' and position_amt > 0:  # Closing long position before sell
                should_close = True
                close_side = 'SELL' 
                logger.info(f"Found long position {position_amt} for {symbol}, will close before sell")
            
            if should_close:
                # Close the position
                close_order = call_binance_api(binance_client.futures_create_order,
                    symbol=symbol,
                    side=close_side,
                    type='MARKET',
                    quantity=close_quantity,
                    reduceOnly=True
                )
                logger.info(f"Closed opposite position: {close_side} {close_quantity} {symbol} - Order ID: {close_order['orderId']}")
                
                # Cancel any existing orders for this symbol to avoid conflicts
                try:
                    existing_orders = call_binance_api(binance_client.futures_get_open_orders, symbol=symbol)
                    for order in existing_orders:
                        call_binance_api(binance_client.futures_cancel_order, symbol=symbol, orderId=order['orderId'])
                        logger.info(f"Cancelled existing order {order['orderId']} for {symbol}")
                except Exception as cancel_error:
                    logger.warning(f"Error cancelling existing orders for {symbol}: {cancel_error}")
                
                return {
                    'success': True, 
                    'message': f'Closed opposite position {close_side} {close_quantity} {symbol}',
                    'closed_order': close_order
                }
        
        logger.info(f"No opposite positions found for {symbol} - proceeding with {new_action}")
        return {'success': True, 'message': 'No opposite positions to close'}
        
    except BinanceAPIException as e:
        logger.error(f"Binance API error while closing opposite position: {e.message}")
        return {'success': False, 'error': f'Binance API error: {e.message}'}
    except Exception as e:
        logger.error(f"Error closing opposite position: {str(e)}")
        return {'success': False, 'error': f'Error closing opposite position: {str(e)}'}

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

def calculate_position_quantity(symbol, balance_percentage=0.20, leverage=10):
    """
    Calculate position quantity based on account balance percentage
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        balance_percentage: Percentage of balance to use (default 20% = 0.20)
        leverage: Leverage multiplier (default 10x)
    
    Returns:
        dict: {'success': bool, 'quantity': float, 'details': dict}
    """
    global binance_client
    
    try:
        logger.info(f"Calculating position quantity for {symbol} using {balance_percentage*100}% of balance with {leverage}x leverage")
        
        # Step 1: Get account balance
        account_info = call_binance_api(binance_client.futures_account)
        total_balance = float(account_info['totalWalletBalance'])
        available_balance = float(account_info['availableBalance'])
        
        logger.info(f"Account balance - Total: {total_balance} USDT, Available: {available_balance} USDT")
        
        # Step 2: Calculate position size in USDT
        position_value_usdt = available_balance * balance_percentage * leverage
        
        logger.info(f"Position value: {available_balance} * {balance_percentage} * {leverage} = {position_value_usdt} USDT")
        
        # Step 3: Get current market price
        ticker = call_binance_api(binance_client.futures_symbol_ticker, symbol=symbol)
        current_price = float(ticker['price'])
        
        logger.info(f"Current {symbol} price: {current_price}")
        
        # Step 4: Calculate quantity
        raw_quantity = position_value_usdt / current_price
        
        # Step 5: Get symbol precision info for rounding
        exchange_info = call_binance_api(binance_client.futures_exchange_info)
        symbol_info = next(s for s in exchange_info['symbols'] if s['symbol'] == symbol)
        lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size_filter['stepSize'])
        
        # Round quantity to appropriate precision
        final_quantity = round(raw_quantity - (raw_quantity % step_size), 8)
        
        logger.info(f"Quantity calculation: {position_value_usdt} USDT / {current_price} = {raw_quantity} -> rounded to {final_quantity}")
        
        # Step 6: Validate minimum quantity
        min_qty = float(lot_size_filter['minQty'])
        if final_quantity < min_qty:
            # Suggest minimum balance needed for this symbol
            min_position_value = min_qty * current_price
            min_balance_needed = min_position_value / leverage
            
            return {
                'success': False,
                'error': f'Calculated quantity {final_quantity} is below minimum {min_qty} for {symbol}. Need at least {min_balance_needed:.2f} USDT available balance (or {min_balance_needed/available_balance*100:.1f}% of current balance) to trade this symbol with {leverage}x leverage.',
                'details': {
                    'calculated_quantity': final_quantity,
                    'minimum_quantity': min_qty,
                    'minimum_balance_needed': min_balance_needed,
                    'minimum_balance_percentage': min_balance_needed/available_balance if available_balance > 0 else 1.0,
                    'position_value_usdt': position_value_usdt,
                    'current_price': current_price,
                    'suggestion': f'Increase balance_percentage to at least {min_balance_needed/available_balance:.3f} or use a different symbol with lower minimum quantity'
                }
            }
        
        return {
            'success': True,
            'quantity': final_quantity,
            'details': {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'balance_percentage': balance_percentage,
                'leverage': leverage,
                'position_value_usdt': position_value_usdt,
                'current_price': current_price,
                'raw_quantity': raw_quantity,
                'final_quantity': final_quantity,
                'step_size': step_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating position quantity: {str(e)}")
        return {
            'success': False,
            'error': f'Failed to calculate position quantity: {str(e)}',
            'details': {}
        }

def handle_close_position(symbol):
    """
    Handle close position signals from pine script
    Close any existing long positions for the symbol
    """
    global binance_client
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured'
        }), 400
    
    try:
        logger.info(f"Processing close signal for {symbol}")
        
        # Get current positions for the symbol
        positions = call_binance_api(binance_client.futures_position_information, symbol=symbol)
        closed_positions = []
        
        for position in positions:
            position_amt = float(position['positionAmt'])
            
            # Close both long and short positions
            if position_amt > 0:
                # Close long position with SELL order
                close_quantity = position_amt
                close_side = 'SELL'
                
                close_order = binance_client.futures_create_order(
                    symbol=symbol,
                    side=close_side,
                    type='MARKET',
                    quantity=close_quantity,
                    reduceOnly=True
                )
                
                closed_positions.append({
                    'quantity': close_quantity,
                    'order_id': close_order.get('orderId'),
                    'side': close_side,
                    'position_type': 'long'
                })
                
                logger.info(f"Closed long position: {close_side} {close_quantity} {symbol} - Order ID: {close_order['orderId']}")
                
            elif position_amt < 0:
                # Close short position with BUY order
                close_quantity = abs(position_amt)  # Convert negative to positive
                close_side = 'BUY'
                
                close_order = call_binance_api(binance_client.futures_create_order,
                    symbol=symbol,
                    side=close_side,
                    type='MARKET',
                    quantity=close_quantity,
                    reduceOnly=True
                )
                
                closed_positions.append({
                    'quantity': close_quantity,
                    'order_id': close_order.get('orderId'),
                    'side': close_side,
                    'position_type': 'short'
                })
                
                logger.info(f"Closed short position: {close_side} {close_quantity} {symbol} - Order ID: {close_order['orderId']}")
        
        # Cancel any existing orders for this symbol
        try:
            existing_orders = call_binance_api(binance_client.futures_get_open_orders, symbol=symbol)
            cancelled_orders = []
            for order in existing_orders:
                call_binance_api(binance_client.futures_cancel_order, symbol=symbol, orderId=order['orderId'])
                cancelled_orders.append(order['orderId'])
                logger.info(f"Cancelled existing order {order['orderId']} for {symbol}")
        except Exception as cancel_error:
            logger.warning(f"Error cancelling existing orders for {symbol}: {cancel_error}")
            cancelled_orders = []
        
        if not closed_positions:
            return jsonify({
                'success': True,
                'message': f'No open positions to close for {symbol}',
                'symbol': symbol,
                'action': 'close',
                'closed_positions': [],
                'cancelled_orders': cancelled_orders,
                'timestamp': datetime.now().isoformat()
            })
        
        # Store close trade record
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'source': 'state_aware_ma_cross_pine_script_close',
            'symbol': symbol,
            'action': 'close',
            'closed_positions': closed_positions,
            'cancelled_orders': cancelled_orders,
            'status': 'completed'
        }
        
        active_orders.append(trade_record)
        
        # Calculate position types for detailed message
        long_positions = sum(1 for p in closed_positions if p['position_type'] == 'long')
        short_positions = sum(1 for p in closed_positions if p['position_type'] == 'short')
        position_summary = []
        if long_positions > 0:
            position_summary.append(f"{long_positions} long")
        if short_positions > 0:
            position_summary.append(f"{short_positions} short")
        
        return jsonify({
            'success': True,
            'message': f'Closed {" and ".join(position_summary)} position(s) for {symbol}' if position_summary else f'Closed {len(closed_positions)} position(s) for {symbol}',
            'symbol': symbol,
            'action': 'close',
            'closed_positions': closed_positions,
            'cancelled_orders': cancelled_orders,
            'total_closed': len(closed_positions),
            'long_positions_closed': long_positions,
            'short_positions_closed': short_positions,
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        logger.error(f"Binance API error while closing positions: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except Exception as e:
        logger.error(f"Error closing positions: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error closing positions: {str(e)}'
        }), 500

@binance_bp.route('/binance/target-trend-webhook', methods=['POST'])
@binance_bp.route('/tradingview/binancebinance/target-trend-webhook', methods=['POST'])  # Handle TradingView alert URL
def target_trend_webhook():
    """
    Webhook endpoint specifically for Target_Trend_V1 pine script
    Handles buy/sell signals with multiple take profit levels
    Closes opposite positions before opening new ones
    """
    global binance_client, active_orders
    
    if not ensure_binance_client():
        return jsonify({
            'success': False,
            'error': 'Binance client initialization failed. Auto-initialization attempted.'
        }), 400
    
    try:
        # Get the webhook data from pine script
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No webhook data received from pine script'
            }), 400
        
        # Extract parameters from dual direction pine script alert
        symbol = str(data.get('symbol', '')).upper()
        action = str(data.get('action', '')).lower()
        # Try 'balance_percentage' first (new format), fallback to 'quantity' (old format)
        balance_percentage = float(data.get('balance_percentage', data.get('quantity', 0)))  # This is percentage of equity (0.20 = 20%)
        leverage = int(data.get('leverage', trading_config['leverage']))
        entry_price = float(data.get('entry', 0))
        
        # Validate required parameters
        if not symbol or action not in ['buy', 'sell']:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol or action in pine script alert. Expected "buy" or "sell"'
            }), 400
        
        # Validate balance percentage (should be between 0.01 and 1.0)
        if balance_percentage <= 0 or balance_percentage > 1.0:
            return jsonify({
                'success': False,
                'error': f'Invalid quantity percentage in pine script alert: {balance_percentage}. Expected 0.01-1.0 (1%-100%)'
            }), 400
        
        # Ensure symbol format is correct
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        logger.info(f"Target Trend webhook received: {action} {balance_percentage*100}% balance ({leverage}x leverage) for {symbol} at {entry_price}")
        
        # Step 1: IMMEDIATELY close opposite position first and wait for confirmation
        logger.info(f"Step 1: Checking and closing opposite positions for {symbol} before {action}")
        close_result = close_opposite_position_immediate(symbol, action)
        if not close_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to close existing position: {close_result["error"]}'
            }), 400
        
        # Wait a moment for position closure to be fully processed
        import time
        if close_result.get('position_closed', False):
            logger.info(f"Waiting 1 second for position closure confirmation...")
            time.sleep(1)
        
        # Step 2: Set leverage for the symbol
        try:
            call_binance_api(binance_client.futures_change_leverage, symbol=symbol, leverage=leverage)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
        except Exception as lev_error:
            logger.warning(f"Could not set leverage for {symbol}: {lev_error}")
        
        # Step 3: Set margin type
        try:
            call_binance_api(binance_client.futures_change_margin_type, symbol=symbol, marginType=trading_config['margin_type'])
            logger.info(f"Margin type set to {trading_config['margin_type']} for {symbol}")
        except Exception as margin_error:
            logger.warning(f"Could not set margin type for {symbol} (may already be set): {margin_error}")
        
        # Step 4: Calculate actual position quantity from percentage and leverage
        logger.info(f"Converting quantity percentage {balance_percentage*100}% with {leverage}x leverage to actual quantity")
        
        quantity_result = calculate_position_quantity(symbol, balance_percentage, leverage)
        
        if not quantity_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to calculate position quantity: {quantity_result["error"]}',
                'details': quantity_result.get('details', {})
            }), 400
        
        quantity = quantity_result['quantity']
        logger.info(f"Calculated quantity: {quantity} {symbol} (from {balance_percentage*100}% balance * {leverage}x leverage)")
        
        # Step 5: IMMEDIATELY execute main entry order with unique client ID
        side = 'BUY' if action == 'buy' else 'SELL'
        
        # Generate unique client order ID for tracking
        import uuid
        client_order_id = f"TT_{action.upper()}_{symbol}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        logger.info(f"Step 5: Executing {action} order immediately after position closure")
        
        main_order = call_binance_api(binance_client.futures_create_order,
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity,
            newClientOrderId=client_order_id
        )
        
        logger.info(f"✅ IMMEDIATE {action.upper()} ORDER EXECUTED: {quantity} {symbol} - Order ID: {main_order.get('orderId')} - Client ID: {client_order_id}")
        
        # Store trade record
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'source': 'target_trend_v1_pine_script_dual_direction',
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'balance_percentage': balance_percentage,
            'leverage': leverage,
            'entry_price': entry_price,
            'main_order': main_order,
            'opposite_position_result': close_result,
            'pine_script_data': data,
            'quantity_calculation': quantity_result['details'],
            'status': 'active',
            'mode': 'dual_direction'
        }
        
        active_orders.append(trade_record)
        
        current_price = call_binance_api(binance_client.futures_symbol_ticker, symbol=symbol)['price']
        
        # Prepare execution summary
        execution_summary = {
            'opposite_positions_closed': close_result.get('position_closed', False),
            'closed_positions_count': len(close_result.get('closed_positions', [])),
            'total_closed_value': close_result.get('total_closed_value', 0),
            'new_order_executed': True,
            'execution_sequence': 'IMMEDIATE: Close opposite positions → Open new position'
        }
        
        return jsonify({
            'success': True,
            'message': f'✅ TARGET TREND {action.upper()} EXECUTED IMMEDIATELY: {quantity} {symbol}',
            'execution_summary': execution_summary,
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'balance_percentage': balance_percentage,
                'balance_percentage_display': f"{balance_percentage*100}%",
                'leverage': leverage,
                'entry_price': entry_price,
                'current_price': float(current_price),
                'main_order_id': main_order.get('orderId'),
                'client_order_id': client_order_id,
                'opposite_positions_closed': close_result.get('closed_positions', []),
                'mode': 'dual_direction_immediate',
                'quantity_calculation': quantity_result['details'],
                'note': f'IMMEDIATE EXECUTION: Closed opposite positions first, then opened {action} position with {balance_percentage*100}% account balance × {leverage}x leverage'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        logger.error(f"Binance API error in Target Trend webhook: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except BinanceOrderException as e:
        logger.error(f"Binance order error in Target Trend webhook: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Order error: {e.message}'
        }), 400
    except Exception as e:
        logger.error(f"Error in Target Trend webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Target Trend webhook error: {str(e)}'
        }), 500

@binance_bp.route('/binance/test-target-trend', methods=['POST'])
def test_target_trend_webhook():
    """Test the Target Trend webhook with sample pine script data"""
    # Sample data that matches the simplified pine script alert format
    sample_buy_signal = {
        "action": "buy",
        "symbol": "BTCUSDT",
        "balance_percentage": "0.20",  # Updated to use new format
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    sample_sell_signal = {
        "action": "sell",
        "symbol": "BTCUSDT", 
        "balance_percentage": "0.20",  # Updated to use new format
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    return jsonify({
        'success': True,
        'message': 'Target Trend webhook test endpoint ready - WITH IMMEDIATE EXECUTION',
        'webhook_url': '/binance/target-trend-webhook',
        'sample_formats': {
            'buy_signal': sample_buy_signal,
            'sell_signal': sample_sell_signal
        },
        'immediate_execution_features': [
            '🚀 IMMEDIATE opposite position closure before new order',
            '⚡ Zero-delay execution sequence',
            '🔄 Automatic order cancellation for clean slate',
            '✅ Real-time position monitoring and confirmation',
            '📊 Detailed execution summary with timing',
            '🎯 Unique client order IDs for precise tracking'
        ],
        'execution_sequence': {
            'step_1': 'Receive signal (buy/sell)',
            'step_2': 'IMMEDIATELY check for opposite positions',
            'step_3': 'IMMEDIATELY close opposite positions with MARKET orders',
            'step_4': 'Cancel all existing TP/SL orders for clean slate',
            'step_5': 'Wait 1 second for position closure confirmation',
            'step_6': 'IMMEDIATELY open new position with calculated quantity',
            'step_7': 'Return detailed execution summary'
        },
        'signal_behavior': {
            'BUY_signal': 'Immediately closes any SHORT positions → Opens LONG position',
            'SELL_signal': 'Immediately closes any LONG positions → Opens SHORT position'
        },
        'features': [
            'Dual direction strategy (long and short positions)',
            'IMMEDIATE opposite position closure with confirmation',
            'Buy signals for long entries, sell signals for short entries',
            'Supports both bullish and bearish market conditions',
            'Respects symbol precision and tick size',
            'Comprehensive order tracking and logging',
            'Enhanced JSON format with balance_percentage'
        ],
        'usage_instructions': {
            'step_1': 'Configure TradingView alert to send to /binance/target-trend-webhook or /tradingview/binancebinance/target-trend-webhook',
            'step_2': 'Set pine script alert message to the raw JSON format (use balance_percentage instead of quantity)',
            'step_3': 'Ensure Binance API credentials are configured with futures trading permissions',
            'step_4': 'Test with small balance_percentage first (e.g., 0.05 = 5%)'
        },
        'supported_urls': [
            '/api/binance/target-trend-webhook',
            '/api/tradingview/binancebinance/target-trend-webhook'
        ],
        'timestamp': datetime.now().isoformat()
    })

@binance_bp.route('/binance/state-aware-ma-cross-webhook', methods=['POST'])
@binance_bp.route('/tradingview/binancebinance/state-aware-ma-cross-webhook', methods=['POST'])  # Handle TradingView alert URL
def state_aware_ma_cross_webhook():
    """
    Webhook endpoint specifically for State-aware MA Cross pine script
    Handles buy/close signals for futures trading
    Closes existing positions before opening new ones
    """
    global binance_client, active_orders
    
    if not ensure_binance_client():
        return jsonify({
            'success': False,
            'error': 'Binance client initialization failed. Auto-initialization attempted.'
        }), 400
    
    try:
        # Get the webhook data from pine script with better error handling
        logger.info(f"State-aware MA Cross webhook called - Content-Type: {request.headers.get('Content-Type', 'Unknown')}")
        
        # Handle different content types
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = request.get_json()
        else:
            # Handle plain text or other formats from TradingView
            raw_data = request.get_data(as_text=True)
            logger.info(f"Raw webhook data received: {raw_data}")
            try:
                import json
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse webhook data as JSON: {raw_data}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON format in webhook data: {raw_data}'
                }), 400
        
        if not data:
            logger.error("No webhook data received from TradingView")
            return jsonify({
                'success': False,
                'error': 'No webhook data received from pine script'
            }), 400
        
        logger.info(f"Parsed webhook data: {data}")
        
        # Extract parameters from State-aware MA Cross pine script alert
        try:
            symbol = str(data.get('symbol', '')).upper()
            action = str(data.get('action', '')).lower()
            # Get balance percentage from webhook data (default 20%)
            # Try 'balance_percentage' first (new format), fallback to 'quantity' (old format)
            balance_percentage = float(data.get('balance_percentage', data.get('quantity', 0.20)))
            leverage = int(data.get('leverage', trading_config['leverage']))
            entry_price = float(data.get('entry', 0))
        except (ValueError, TypeError) as param_error:
            logger.error(f"Error parsing webhook parameters: {param_error}, data: {data}")
            return jsonify({
                'success': False,
                'error': f'Invalid parameter format in webhook data: {str(param_error)}'
            }), 400
        
        # Validate required parameters
        if not symbol or action not in ['buy', 'sell', 'close']:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol or action in pine script alert. Expected "buy", "sell", or "close"'
            }), 400
        
        # Validate balance percentage
        if action in ['buy', 'sell'] and (balance_percentage <= 0 or balance_percentage > 1):
            return jsonify({
                'success': False,
                'error': 'Invalid balance_percentage. Must be between 0.01 (1%) and 1.0 (100%)'
            }), 400
        
        # Ensure symbol format is correct
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        logger.info(f"State-aware MA Cross webhook received: {action} {symbol} using {balance_percentage*100}% balance at {entry_price}")
        
        # Handle close action differently
        if action == 'close':
            return handle_close_position(symbol)
        
        # Step 1: Calculate position quantity based on account balance
        quantity_result = calculate_position_quantity(symbol, balance_percentage, leverage)
        if not quantity_result['success']:
            # Log the specific error for debugging
            logger.error(f"Quantity calculation failed for {symbol}: {quantity_result['error']}")
            logger.error(f"Details: {quantity_result.get('details', {})}")
            
            return jsonify({
                'success': False,
                'error': f'Failed to calculate position quantity: {quantity_result["error"]}',
                'details': quantity_result['details'],
                'webhook_data': data  # Include original webhook data for debugging
            }), 400
        
        quantity = quantity_result['quantity']
        calculation_details = quantity_result['details']
        
        logger.info(f"Calculated quantity: {quantity} {symbol} (Position value: {calculation_details['position_value_usdt']} USDT)")
        
        # Step 2: Close opposite position first
        close_result = close_opposite_position(symbol, action)
        if not close_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to close existing position: {close_result["error"]}'
            }), 400
        
        # Step 3: Set leverage for the symbol
        try:
            call_binance_api(binance_client.futures_change_leverage, symbol=symbol, leverage=leverage)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
        except Exception as lev_error:
            logger.warning(f"Could not set leverage for {symbol}: {lev_error}")
        
        # Step 4: Set margin type
        try:
            call_binance_api(binance_client.futures_change_margin_type, symbol=symbol, marginType=trading_config['margin_type'])
            logger.info(f"Margin type set to {trading_config['margin_type']} for {symbol}")
        except Exception as margin_error:
            logger.warning(f"Could not set margin type for {symbol} (may already be set): {margin_error}")
        
        # Step 5: Place the main market order (buy or sell)
        order_side = SIDE_BUY if action == 'buy' else SIDE_SELL
        main_order = call_binance_api(binance_client.futures_create_order,
            symbol=symbol,
            side=order_side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        
        logger.info(f"State-aware MA Cross {action} order placed: {main_order}")
        
        # Get current price for response
        current_price = call_binance_api(binance_client.futures_symbol_ticker, symbol=symbol)['price']
        
        return jsonify({
            'success': True,
            'message': f'State-aware MA Cross order executed: {action} {quantity} {symbol} (auto-calculated quantity)',
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'leverage': leverage,
                'entry_price': entry_price,
                'current_price': float(current_price),
                'main_order_id': main_order.get('orderId'),
                'opposite_position_closed': close_result.get('message', 'No opposite positions'),
                'mode': 'auto_quantity',
                'note': 'Quantity auto-calculated based on account balance percentage'
            },
            'calculation_details': calculation_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_message = getattr(e, 'message', str(e))
        
        logger.error(f"Binance API error in State-aware MA Cross webhook: Code {error_code} - {error_message}")
        
        # Provide specific guidance based on error codes
        suggestions = []
        if error_code == -1121:  # Invalid symbol
            suggestions.append("Check if the symbol exists and is available for futures trading")
        elif error_code == -1111:  # Precision error
            suggestions.append("Check quantity precision - use proper decimal places")
        elif error_code == -2010:  # Insufficient balance
            suggestions.append("Increase your account balance or reduce position size")
        elif error_code == -1013:  # Invalid quantity (too small/large)
            suggestions.append("Adjust balance_percentage - quantity may be too small or too large for this symbol")
        elif error_code == -4131:  # Percent price protection
            suggestions.append("Market price moved too much - retry with current market conditions")
        
        return jsonify({
            'success': False,
            'error': f'Binance API error (Code {error_code}): {error_message}',
            'suggestions': suggestions,
            'webhook_data': data
        }), 400
    except BinanceOrderException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_message = getattr(e, 'message', str(e))
        
        logger.error(f"Binance order error in State-aware MA Cross webhook: Code {error_code} - {error_message}")
        
        return jsonify({
            'success': False,
            'error': f'Order error (Code {error_code}): {error_message}',
            'webhook_data': data
        }), 400
    except Exception as e:
        logger.error(f"Error in State-aware MA Cross webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'State-aware MA Cross webhook error: {str(e)}'
        }), 500

@binance_bp.route('/binance/smart-webhook', methods=['POST'])
@binance_bp.route('/tradingview/binance/smart-webhook', methods=['POST']) 
def smart_webhook():
    """
    Smart webhook endpoint with configurable quantity percentage and leverage
    Defaults: quantity_percent = 20%, leverage = 10x
    Automatically converts percentage to real quantity for the specific symbol
    """
    global binance_client, active_orders
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured. Please configure API credentials first.'
        }), 400
    
    try:
        # Get the webhook data
        logger.info(f"Smart webhook called - Content-Type: {request.headers.get('Content-Type', 'Unknown')}")
        
        # Handle different content types
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = request.get_json()
        else:
            # Handle plain text or other formats from TradingView
            raw_data = request.get_data(as_text=True)
            logger.info(f"Raw webhook data received: {raw_data}")
            try:
                import json
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse webhook data as JSON: {raw_data}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON format in webhook data: {raw_data}'
                }), 400
        
        if not data:
            logger.error("No webhook data received from TradingView")
            return jsonify({
                'success': False,
                'error': 'No webhook data received'
            }), 400
        
        logger.info(f"Parsed smart webhook data: {data}")
        
        # Extract parameters with defaults
        try:
            symbol = str(data.get('symbol', '')).upper()
            action = str(data.get('action', '')).lower()
            
            # Set defaults: 20% quantity, 10x leverage
            quantity_percent = float(data.get('quantity_percent', data.get('balance_percentage', 0.20)))  # Default 20%
            leverage = int(data.get('leverage', 10))  # Default 10x leverage
            
            entry_price = float(data.get('entry', data.get('price', 0)))
            
            # Optional stop loss and take profit percentages
            sl_percent = float(data.get('sl_percent', trading_config.get('default_sl_percentage', 1.0)))
            tp_percent = float(data.get('tp_percent', trading_config.get('default_tp_percentage', 2.0)))
            
        except (ValueError, TypeError) as param_error:
            logger.error(f"Error parsing smart webhook parameters: {param_error}, data: {data}")
            return jsonify({
                'success': False,
                'error': f'Invalid parameter format in webhook data: {str(param_error)}'
            }), 400
        
        # Validate required parameters
        if not symbol or action not in ['buy', 'sell', 'long', 'short', 'close']:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol or action. Expected "buy", "sell", "long", "short", or "close"'
            }), 400
        
        # Normalize action (long = buy, short = sell)
        if action == 'long':
            action = 'buy'
        elif action == 'short':
            action = 'sell'
        
        # Validate quantity percentage
        if action in ['buy', 'sell'] and (quantity_percent <= 0 or quantity_percent > 1):
            return jsonify({
                'success': False,
                'error': 'Invalid quantity_percent. Must be between 0.01 (1%) and 1.0 (100%)'
            }), 400
        
        # Ensure symbol format is correct
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        logger.info(f"Smart webhook processing: {action} {symbol} using {quantity_percent*100}% balance with {leverage}x leverage")
        
        # Handle close action differently
        if action == 'close':
            return handle_close_position(symbol)
        
        # Step 1: Get symbol requirements and validate feasibility
        symbol_requirements = get_symbol_minimum_requirements(symbol)
        if not symbol_requirements['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to get symbol requirements: {symbol_requirements["error"]}'
            }), 400
        
        # Step 2: Calculate position quantity based on account balance
        quantity_result = calculate_position_quantity(symbol, quantity_percent, leverage)
        if not quantity_result['success']:
            # Log the specific error for debugging
            logger.error(f"Quantity calculation failed for {symbol}: {quantity_result['error']}")
            logger.error(f"Details: {quantity_result.get('details', {})}")
            
            # Suggest alternative percentage if minimum not met
            suggestions = []
            details = quantity_result.get('details', {})
            if 'minimum_balance_percentage' in details:
                min_percent = details['minimum_balance_percentage']
                suggestions.append(f"Try using quantity_percent: {min_percent:.3f} (minimum {min_percent*100:.1f}%)")
            
            return jsonify({
                'success': False,
                'error': f'Failed to calculate position quantity: {quantity_result["error"]}',
                'details': quantity_result['details'],
                'suggestions': suggestions,
                'webhook_data': data
            }), 400
        
        quantity = quantity_result['quantity']
        calculation_details = quantity_result['details']
        
        logger.info(f"Calculated quantity: {quantity} {symbol} (Position value: {calculation_details['position_value_usdt']} USDT)")
        
        # Step 3: Close opposite position first
        close_result = close_opposite_position(symbol, action)
        if not close_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to close existing position: {close_result["error"]}'
            }), 400
        
        # Step 4: Set leverage for the symbol
        try:
            call_binance_api(binance_client.futures_change_leverage, symbol=symbol, leverage=leverage)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
        except Exception as lev_error:
            logger.warning(f"Could not set leverage for {symbol}: {lev_error}")
        
        # Step 5: Set margin type
        try:
            call_binance_api(binance_client.futures_change_margin_type, symbol=symbol, marginType=trading_config['margin_type'])
            logger.info(f"Margin type set to {trading_config['margin_type']} for {symbol}")
        except Exception as margin_error:
            logger.warning(f"Could not set margin type for {symbol} (may already be set): {margin_error}")
        
        # Step 6: Place the main market order (buy or sell)
        order_side = SIDE_BUY if action == 'buy' else SIDE_SELL
        main_order = call_binance_api(binance_client.futures_create_order,
            symbol=symbol,
            side=order_side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        
        logger.info(f"Smart webhook {action} order placed: {main_order}")
        
        # Get current price for response
        current_price = call_binance_api(binance_client.futures_symbol_ticker, symbol=symbol)['price']
        
        # Calculate real quantities and prices for SL/TP if provided
        entry_fill_price = float(current_price)  # Use current price as approximate fill price
        
        sl_price = None
        tp_price = None
        if action == 'buy':
            sl_price = entry_fill_price * (1 - sl_percent / 100) if sl_percent > 0 else None
            tp_price = entry_fill_price * (1 + tp_percent / 100) if tp_percent > 0 else None
        else:  # sell
            sl_price = entry_fill_price * (1 + sl_percent / 100) if sl_percent > 0 else None
            tp_price = entry_fill_price * (1 - tp_percent / 100) if tp_percent > 0 else None
        
        return jsonify({
            'success': True,
            'message': f'Smart webhook order executed: {action} {quantity} {symbol}',
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'quantity_percent': quantity_percent,
                'quantity_percent_display': f"{quantity_percent*100}%",
                'leverage': leverage,
                'entry_price': entry_price,
                'current_price': float(current_price),
                'estimated_fill_price': entry_fill_price,
                'main_order_id': main_order.get('orderId'),
                'opposite_position_closed': close_result.get('message', 'No opposite positions'),
                'stop_loss': {
                    'enabled': sl_percent > 0,
                    'percent': sl_percent,
                    'price': sl_price
                },
                'take_profit': {
                    'enabled': tp_percent > 0,
                    'percent': tp_percent,
                    'price': tp_price
                },
                'mode': 'smart_webhook',
                'note': f'Quantity: {quantity_percent*100}% of balance converted to {quantity} {symbol}'
            },
            'calculation_details': calculation_details,
            'symbol_requirements': {
                'min_quantity': symbol_requirements['min_qty'],
                'step_size': symbol_requirements['step_size'],
                'min_notional': symbol_requirements.get('min_notional', 'N/A')
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_message = getattr(e, 'message', str(e))
        
        logger.error(f"Binance API error in smart webhook: Code {error_code} - {error_message}")
        
        # Provide specific guidance based on error codes
        suggestions = []
        if error_code == -1121:  # Invalid symbol
            suggestions.append("Check if the symbol exists and is available for futures trading")
        elif error_code == -1111:  # Precision error
            suggestions.append("Check quantity precision - use proper decimal places")
        elif error_code == -2010:  # Insufficient balance
            suggestions.append("Increase your account balance or reduce quantity_percent")
        elif error_code == -1013:  # Invalid quantity (too small/large)
            suggestions.append("Adjust quantity_percent - calculated quantity may be too small or too large for this symbol")
        elif error_code == -4131:  # Percent price protection
            suggestions.append("Market price moved too much - retry with current market conditions")
        
        return jsonify({
            'success': False,
            'error': f'Binance API error (Code {error_code}): {error_message}',
            'suggestions': suggestions,
            'webhook_data': data
        }), 400
    except BinanceOrderException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_message = getattr(e, 'message', str(e))
        
        logger.error(f"Binance order error in smart webhook: Code {error_code} - {error_message}")
        
        return jsonify({
            'success': False,
            'error': f'Order error (Code {error_code}): {error_message}',
            'webhook_data': data
        }), 400
    except Exception as e:
        logger.error(f"Error in smart webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Smart webhook error: {str(e)}'
        }), 500

@binance_bp.route('/binance/super-scalper-webhook', methods=['POST'])
@binance_bp.route('/tradingview/binance/super-scalper-webhook', methods=['POST'])
def super_scalper_webhook():
    """
    Professional Crypto Super Scalper webhook endpoint
    Supports advanced multi-factor trading signals with position management
    Handles: Long Entry, Short Entry, Exit All, Risk Management
    """
    global binance_client, active_orders
    
    if not ensure_binance_client():
        return jsonify({
            'success': False,
            'error': 'Binance client initialization failed. Auto-initialization attempted.'
        }), 400
    
    try:
        # Get the webhook data
        logger.info(f"Super Scalper webhook called - Content-Type: {request.headers.get('Content-Type', 'Unknown')}")
        
        # Handle different content types
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = request.get_json()
        else:
            # Handle plain text or other formats from TradingView
            raw_data = request.get_data(as_text=True)
            logger.info(f"Raw Super Scalper webhook data received: {raw_data}")
            try:
                import json
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Super Scalper webhook data as JSON: {raw_data}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON format in webhook data: {raw_data}'
                }), 400
        
        if not data:
            logger.error("No webhook data received from Super Scalper strategy")
            return jsonify({
                'success': False,
                'error': 'No webhook data received from Super Scalper strategy'
            }), 400
        
        logger.info(f"Parsed Super Scalper webhook data: {data}")
        
        # Extract parameters with Super Scalper specific defaults
        try:
            symbol = str(data.get('symbol', '')).upper()
            action = str(data.get('action', '')).lower()
            
            # Super Scalper specific settings (aggressive scalping parameters)
            quantity_percent = float(data.get('quantity_percent', data.get('balance_percentage', 0.15)))  # Default 15% for scalping
            leverage = int(data.get('leverage', 20))  # Default 20x leverage for scalping
            
            entry_price = float(data.get('entry', data.get('price', 0)))
            
            # Super Scalper risk management (tighter stops, quicker profits)
            sl_percent = float(data.get('sl_percent', 0.8))  # Tighter stop loss for scalping
            tp_percent = float(data.get('tp_percent', 1.2))  # Quick take profit for scalping
            
            # Super Scalper specific parameters
            risk_level = str(data.get('risk_level', 'medium')).lower()  # low, medium, high
            signal_strength = str(data.get('signal_strength', 'normal')).lower()  # weak, normal, strong
            market_condition = str(data.get('market_condition', 'normal')).lower()  # trending, ranging, volatile, normal
            
        except (ValueError, TypeError) as param_error:
            logger.error(f"Error parsing Super Scalper webhook parameters: {param_error}, data: {data}")
            return jsonify({
                'success': False,
                'error': f'Invalid parameter format in Super Scalper webhook data: {str(param_error)}'
            }), 400
        
        # Validate required parameters
        if not symbol or action not in ['buy', 'sell', 'long', 'short', 'close', 'exit', 'emergency_exit']:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol or action. Super Scalper expects: "buy", "sell", "long", "short", "close", "exit", or "emergency_exit"'
            }), 400
        
        # Normalize action (long = buy, short = sell)
        if action == 'long':
            action = 'buy'
        elif action == 'short':
            action = 'sell'
        elif action in ['exit', 'emergency_exit']:
            action = 'close'
        
        # Adjust position size based on signal strength and risk level
        if signal_strength == 'strong':
            quantity_percent *= 1.5  # Increase position for strong signals
        elif signal_strength == 'weak':
            quantity_percent *= 0.7  # Reduce position for weak signals
            
        if risk_level == 'high':
            quantity_percent *= 0.6  # Reduce position for high risk
            leverage = min(leverage, 10)  # Cap leverage for high risk
        elif risk_level == 'low':
            quantity_percent *= 1.2  # Slightly increase for low risk
        
        # Market condition adjustments
        if market_condition == 'volatile':
            sl_percent *= 1.5  # Wider stops in volatile markets
            tp_percent *= 0.8  # Quicker profits in volatile markets
        elif market_condition == 'ranging':
            tp_percent *= 1.3  # Wider targets in ranging markets
        
        # Validate adjusted quantity percentage
        quantity_percent = min(quantity_percent, 0.5)  # Cap at 50% for safety
        if action in ['buy', 'sell'] and (quantity_percent <= 0 or quantity_percent > 0.5):
            return jsonify({
                'success': False,
                'error': 'Invalid quantity_percent after adjustments. Must be between 0.01 (1%) and 0.5 (50%) for Super Scalper'
            }), 400
        
        # Ensure symbol format is correct
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        logger.info(f"Super Scalper processing: {action} {symbol} using {quantity_percent*100:.1f}% balance with {leverage}x leverage")
        logger.info(f"Signal strength: {signal_strength}, Risk level: {risk_level}, Market condition: {market_condition}")
        
        # Handle close/exit actions
        if action == 'close':
            close_result = close_all_positions_for_symbol(symbol)
            return jsonify({
                'success': True,
                'message': f'Super Scalper close executed for {symbol}',
                'action': 'close_all',
                'symbol': symbol,
                'closed_positions': close_result.get('details', []),
                'signal_info': {
                    'signal_strength': signal_strength,
                    'risk_level': risk_level,
                    'market_condition': market_condition
                },
                'timestamp': datetime.now().isoformat()
            })
        
        # Step 1: Get symbol requirements and validate feasibility
        symbol_requirements = get_symbol_minimum_requirements(symbol)
        if not symbol_requirements['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to get symbol requirements: {symbol_requirements["error"]}'
            }), 400
        
        # Step 2: Calculate position quantity based on account balance
        quantity_result = calculate_position_quantity(symbol, quantity_percent, leverage)
        if not quantity_result['success']:
            # Log the specific error for debugging
            logger.error(f"Super Scalper quantity calculation failed for {symbol}: {quantity_result['error']}")
            logger.error(f"Details: {quantity_result.get('details', {})}")
            
            # Suggest alternative percentage if minimum not met
            suggestions = []
            details = quantity_result.get('details', {})
            if 'minimum_balance_percentage' in details:
                min_percent = details['minimum_balance_percentage']
                suggestions.append(f"Try using quantity_percent: {min_percent:.3f} (minimum {min_percent*100:.1f}%)")
            
            return jsonify({
                'success': False,
                'error': f'Super Scalper quantity calculation failed: {quantity_result["error"]}',
                'details': quantity_result['details'],
                'suggestions': suggestions,
                'webhook_data': data
            }), 400
        
        quantity = quantity_result['quantity']
        calculation_details = quantity_result['details']
        
        logger.info(f"Super Scalper calculated quantity: {quantity} {symbol} (Position value: {calculation_details['position_value_usdt']} USDT)")
        
        # Step 3: Close opposite position first (important for scalping)
        close_result = close_opposite_position(symbol, action)
        if not close_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to close existing position: {close_result["error"]}'
            }), 400
        
        # Step 4: Set leverage for the symbol
        try:
            call_binance_api(binance_client.futures_change_leverage, symbol=symbol, leverage=leverage)
            logger.info(f"Super Scalper leverage set to {leverage}x for {symbol}")
        except Exception as lev_error:
            logger.warning(f"Could not set leverage for {symbol}: {lev_error}")
        
        # Step 5: Set margin type to ISOLATED for scalping (better risk control)
        try:
            call_binance_api(binance_client.futures_change_margin_type, symbol=symbol, marginType='ISOLATED')
            logger.info(f"Super Scalper margin type set to ISOLATED for {symbol}")
        except Exception as margin_error:
            logger.warning(f"Could not set margin type for {symbol} (may already be set): {margin_error}")
        
        # Step 6: Place the main market order (buy or sell)
        order_side = SIDE_BUY if action == 'buy' else SIDE_SELL
        main_order = call_binance_api(binance_client.futures_create_order,
            symbol=symbol,
            side=order_side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        
        logger.info(f"Super Scalper {action} order placed: {main_order}")
        
        # Get current price for response
        current_price = call_binance_api(binance_client.futures_symbol_ticker, symbol=symbol)['price']
        
        # Calculate real quantities and prices for SL/TP
        entry_fill_price = float(current_price)  # Use current price as approximate fill price
        
        sl_price = None
        tp_price = None
        if action == 'buy':
            sl_price = entry_fill_price * (1 - sl_percent / 100) if sl_percent > 0 else None
            tp_price = entry_fill_price * (1 + tp_percent / 100) if tp_percent > 0 else None
        else:  # sell
            sl_price = entry_fill_price * (1 + sl_percent / 100) if sl_percent > 0 else None
            tp_price = entry_fill_price * (1 - tp_percent / 100) if tp_percent > 0 else None
        
        # Place stop loss and take profit orders for scalping
        sl_order_id = None
        tp_order_id = None
        
        try:
            if sl_price:
                sl_side = SIDE_SELL if action == 'buy' else SIDE_BUY
                sl_order = call_binance_api(binance_client.futures_create_order,
                    symbol=symbol,
                    side=sl_side,
                    type=ORDER_TYPE_STOP_MARKET,
                    quantity=quantity,
                    stopPrice=sl_price,
                    reduceOnly=True
                )
                sl_order_id = sl_order.get('orderId')
                logger.info(f"Super Scalper stop loss placed at {sl_price}")
        except Exception as sl_error:
            logger.warning(f"Could not place stop loss: {sl_error}")
        
        try:
            if tp_price:
                tp_side = SIDE_SELL if action == 'buy' else SIDE_BUY
                tp_order = call_binance_api(binance_client.futures_create_order,
                    symbol=symbol,
                    side=tp_side,
                    type=ORDER_TYPE_LIMIT,
                    quantity=quantity,
                    price=tp_price,
                    timeInForce=TIME_IN_FORCE_GTC,
                    reduceOnly=True
                )
                tp_order_id = tp_order.get('orderId')
                logger.info(f"Super Scalper take profit placed at {tp_price}")
        except Exception as tp_error:
            logger.warning(f"Could not place take profit: {tp_error}")
        
        return jsonify({
            'success': True,
            'message': f'Super Scalper order executed: {action} {quantity} {symbol}',
            'trade': {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'quantity_percent': quantity_percent,
                'quantity_percent_display': f"{quantity_percent*100:.1f}%",
                'leverage': leverage,
                'entry_price': entry_price,
                'current_price': float(current_price),
                'estimated_fill_price': entry_fill_price,
                'main_order_id': main_order.get('orderId'),
                'stop_loss_order_id': sl_order_id,
                'take_profit_order_id': tp_order_id,
                'opposite_position_closed': close_result.get('message', 'No opposite positions'),
                'stop_loss': {
                    'enabled': sl_percent > 0,
                    'percent': sl_percent,
                    'price': sl_price
                },
                'take_profit': {
                    'enabled': tp_percent > 0,
                    'percent': tp_percent,
                    'price': tp_price
                },
                'mode': 'super_scalper',
                'note': f'Professional scalping with {quantity_percent*100:.1f}% position size'
            },
            'signal_analysis': {
                'signal_strength': signal_strength,
                'risk_level': risk_level,
                'market_condition': market_condition,
                'adjusted_quantity': f"Original: {data.get('quantity_percent', 0.15)*100:.1f}%, Adjusted: {quantity_percent*100:.1f}%",
                'risk_adjustments': {
                    'sl_adjusted': market_condition == 'volatile',
                    'tp_adjusted': market_condition in ['volatile', 'ranging'],
                    'size_adjusted': signal_strength != 'normal' or risk_level != 'medium'
                }
            },
            'calculation_details': calculation_details,
            'symbol_requirements': {
                'min_quantity': symbol_requirements['min_qty'],
                'step_size': symbol_requirements['step_size'],
                'min_notional': symbol_requirements.get('min_notional', 'N/A')
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_message = getattr(e, 'message', str(e))
        
        logger.error(f"Binance API error in Super Scalper webhook: Code {error_code} - {error_message}")
        
        # Provide specific guidance based on error codes
        suggestions = []
        if error_code == -1121:  # Invalid symbol
            suggestions.append("Check if the symbol exists and is available for futures trading")
        elif error_code == -1111:  # Precision error
            suggestions.append("Check quantity precision - use proper decimal places")
        elif error_code == -2010:  # Insufficient balance
            suggestions.append("Increase your account balance or reduce quantity_percent")
        elif error_code == -1013:  # Invalid quantity (too small/large)
            suggestions.append("Adjust quantity_percent - calculated quantity may be too small or too large for this symbol")
        elif error_code == -4131:  # Percent price protection
            suggestions.append("Market price moved too much - retry with current market conditions")
        
        return jsonify({
            'success': False,
            'error': f'Binance API error (Code {error_code}): {error_message}',
            'suggestions': suggestions,
            'webhook_data': data
        }), 400
    except BinanceOrderException as e:
        error_code = getattr(e, 'code', 'Unknown')
        error_message = getattr(e, 'message', str(e))
        
        logger.error(f"Binance order error in Super Scalper webhook: Code {error_code} - {error_message}")
        
        return jsonify({
            'success': False,
            'error': f'Order error (Code {error_code}): {error_message}',
            'webhook_data': data
        }), 400
    except Exception as e:
        logger.error(f"Error in Super Scalper webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Super Scalper webhook error: {str(e)}'
        }), 500

def close_all_positions_for_symbol(symbol):
    """
    Close all positions for a specific symbol (for Super Scalper exit signals)
    """
    global binance_client
    
    try:
        # Get current positions
        positions = call_binance_api(binance_client.futures_position_information, symbol=symbol)
        closed_positions = []
        
        for position in positions:
            position_amt = float(position['positionAmt'])
            if abs(position_amt) > 0:  # Position exists
                # Determine close side
                close_side = SIDE_SELL if position_amt > 0 else SIDE_BUY
                close_qty = abs(position_amt)
                
                # Place market order to close position
                close_order = call_binance_api(binance_client.futures_create_order,
                    symbol=symbol,
                    side=close_side,
                    type=ORDER_TYPE_MARKET,
                    quantity=close_qty,
                    reduceOnly=True
                )
                
                closed_positions.append({
                    'position_type': 'long' if position_amt > 0 else 'short',
                    'side': close_side,
                    'quantity': close_qty,
                    'order_id': close_order.get('orderId'),
                    'entry_price': float(position['entryPrice']),
                    'mark_price': float(position['markPrice']),
                    'pnl': float(position['unRealizedPnl'])
                })
                
                logger.info(f"Closed {'long' if position_amt > 0 else 'short'} position: {close_qty} {symbol}")
        
        # Cancel any open orders for this symbol
        try:
            open_orders = call_binance_api(binance_client.futures_get_open_orders, symbol=symbol)
            for order in open_orders:
                call_binance_api(binance_client.futures_cancel_order, 
                    symbol=symbol, 
                    orderId=order['orderId']
                )
                logger.info(f"Cancelled open order: {order['orderId']} for {symbol}")
        except Exception as cancel_error:
            logger.warning(f"Could not cancel some orders for {symbol}: {cancel_error}")
        
        return {
            'success': True,
            'message': f'Closed {len(closed_positions)} position(s) for {symbol}',
            'details': closed_positions
        }
        
    except Exception as e:
        logger.error(f"Error closing positions for {symbol}: {str(e)}")
        return {
            'success': False,
            'error': f'Failed to close positions for {symbol}: {str(e)}'
        }

@binance_bp.route('/binance/test-super-scalper-webhook', methods=['POST'])
def test_super_scalper_webhook():
    """Test the Super Scalper webhook with sample professional scalping data"""
    # Sample data for different Super Scalper scenarios
    sample_strong_long = {
        "action": "long",
        "symbol": "ETHUSDT",
        "quantity_percent": 0.15,  # 15% base position
        "leverage": 20,  # Aggressive scalping leverage
        "entry": "3456.78",
        "signal_strength": "strong",  # Will increase position size
        "risk_level": "medium",
        "market_condition": "trending",
        "sl_percent": 0.8,  # Tight stop for scalping
        "tp_percent": 1.2   # Quick profit target
    }
    
    sample_weak_short = {
        "action": "short",
        "symbol": "BTCUSDT",
        "quantity_percent": 0.12,  # 12% base position
        "leverage": 15,
        "entry": "67890.12",
        "signal_strength": "weak",   # Will reduce position size
        "risk_level": "high",       # Will further reduce and cap leverage
        "market_condition": "volatile", # Will adjust stops/targets
        "sl_percent": 0.8,
        "tp_percent": 1.2
    }
    
    sample_emergency_exit = {
        "action": "emergency_exit",
        "symbol": "ADAUSDT",
        "signal_strength": "strong",
        "risk_level": "high",
        "market_condition": "volatile"
    }
    
    sample_ranging_market = {
        "action": "buy",
        "symbol": "DOGEUSDT",
        "quantity_percent": 0.10,
        "leverage": 12,
        "entry": "0.08234",
        "signal_strength": "normal",
        "risk_level": "low",
        "market_condition": "ranging",  # Will adjust targets
        "sl_percent": 0.8,
        "tp_percent": 1.2
    }
    
    return jsonify({
        'success': True,
        'message': 'Super Scalper webhook test endpoint ready',
        'webhook_url': '/binance/super-scalper-webhook',
        'alternative_url': '/tradingview/binance/super-scalper-webhook',
        'scalping_defaults': {
            'quantity_percent': 0.15,  # 15% for aggressive scalping
            'leverage': 20,           # High leverage for scalping
            'sl_percent': 0.8,        # Tight stop loss
            'tp_percent': 1.2,        # Quick take profit
            'margin_type': 'ISOLATED' # Better risk control
        },
        'sample_formats': {
            'strong_long_signal': sample_strong_long,
            'weak_short_signal': sample_weak_short,
            'emergency_exit': sample_emergency_exit,
            'ranging_market': sample_ranging_market
        },
        'signal_parameters': {
            'signal_strength': ['weak', 'normal', 'strong'],
            'risk_level': ['low', 'medium', 'high'],
            'market_condition': ['trending', 'ranging', 'volatile', 'normal']
        },
        'auto_adjustments': {
            'position_sizing': {
                'strong_signals': '+50% size',
                'weak_signals': '-30% size',
                'high_risk': '-40% size',
                'low_risk': '+20% size'
            },
            'risk_management': {
                'volatile_markets': '+50% stop loss width',
                'ranging_markets': '+30% take profit targets',
                'high_risk_mode': 'Max 10x leverage'
            }
        },
        'features': [
            'Professional scalping position sizes (15% default)',
            'High leverage support (20x default)',
            'Automatic position sizing based on signal strength',
            'Risk level adjustments (high risk = smaller positions)',
            'Market condition adaptations (volatile = wider stops)',
            'Emergency exit functionality',
            'Automatic stop loss and take profit placement',
            'ISOLATED margin for better risk control',
            'Multi-factor signal analysis',
            'Professional risk management'
        ],
        'usage_examples': {
            'pine_script_long': {
                'condition': 'enter_long and signal_strength == "strong"',
                'alert_message': '{"action": "long", "symbol": "{{ticker}}", "entry": "{{close}}", "signal_strength": "strong", "market_condition": "trending"}'
            },
            'pine_script_short': {
                'condition': 'enter_short and signal_strength == "normal"',
                'alert_message': '{"action": "short", "symbol": "{{ticker}}", "entry": "{{close}}", "signal_strength": "normal", "risk_level": "medium"}'
            },
            'pine_script_exit': {
                'condition': 'drawdown_exceeded or emergency_conditions',
                'alert_message': '{"action": "emergency_exit", "symbol": "{{ticker}}"}'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@binance_bp.route('/binance/test-smart-webhook', methods=['POST'])
def test_smart_webhook():
    """Test the smart webhook with sample data"""
    # Sample data for the smart webhook
    sample_buy_signal = {
        "action": "buy",
        "symbol": "BTCUSDT",
        "quantity_percent": 0.20,  # 20% of account balance (default)
        "leverage": 10,  # 10x leverage (default)
        "entry": "67000.50",
        "sl_percent": 1.5,  # 1.5% stop loss
        "tp_percent": 3.0   # 3% take profit
    }
    
    sample_sell_signal = {
        "action": "sell",
        "symbol": "ETHUSDT", 
        "quantity_percent": 0.15,  # 15% of account balance
        "leverage": 8,   # 8x leverage
        "entry": "3500.25"
    }
    
    sample_long_signal = {
        "action": "long",  # Alias for buy
        "symbol": "ADAUSDT",
        # Using defaults: 20% quantity, 10x leverage
        "entry": "0.45"
    }
    
    sample_close_signal = {
        "action": "close",
        "symbol": "BTCUSDT"
    }
    
    return jsonify({
        'success': True,
        'message': 'Smart webhook test endpoint ready',
        'webhook_url': '/binance/smart-webhook',
        'alternative_url': '/tradingview/binance/smart-webhook',
        'defaults': {
            'quantity_percent': 0.20,  # 20%
            'leverage': 10,
            'sl_percent': trading_config.get('default_sl_percentage', 1.0),
            'tp_percent': trading_config.get('default_tp_percentage', 2.0)
        },
        'sample_formats': {
            'buy_signal': sample_buy_signal,
            'sell_signal': sample_sell_signal,
            'long_signal': sample_long_signal,
            'close_signal': sample_close_signal
        },
        'features': [
            'Configurable quantity percentage (default 20%)',
            'Configurable leverage (default 10x)',
            'Auto-converts percentage to real quantity for any symbol',
            'Supports buy/sell/long/short/close actions',
            'Optional stop loss and take profit percentages',
            'Validates minimum quantity requirements',
            'Closes opposite positions before opening new ones',
            'Comprehensive error handling with suggestions',
            'Works with any USDT futures pair'
        ],
        'usage_examples': {
            'minimal': {
                'action': 'buy',
                'symbol': 'BTCUSDT'
                # Uses defaults: 20% quantity, 10x leverage
            },
            'custom': {
                'action': 'sell',
                'symbol': 'ETHUSDT',
                'quantity_percent': 0.30,  # 30%
                'leverage': 15,
                'sl_percent': 2.0,
                'tp_percent': 4.0
            }
        },
        'pine_script_integration': {
            'buy_alert': '{"action": "buy", "symbol": "' + '{{ticker}}' + '", "entry": "' + '{{close}}' + '"}',
            'sell_alert': '{"action": "sell", "symbol": "' + '{{ticker}}' + '", "entry": "' + '{{close}}' + '"}',
            'custom_alert': '{"action": "buy", "symbol": "' + '{{ticker}}' + '", "quantity_percent": 0.25, "leverage": 12, "entry": "' + '{{close}}' + '"}'
        },
        'timestamp': datetime.now().isoformat()
    })

@binance_bp.route('/binance/test-state-aware-ma-cross', methods=['POST'])
def test_state_aware_ma_cross_webhook():
    """Test the State-aware MA Cross webhook with sample pine script data"""
    # Sample data that matches the State-aware MA Cross pine script alert format
    sample_buy_signal = {
        "action": "buy",
        "symbol": "BTCUSDT",
        "balance_percentage": "0.20",  # 20% of account balance
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    sample_sell_signal = {
        "action": "sell",
        "symbol": "BTCUSDT",
        "balance_percentage": "0.20",  # 20% of account balance
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    sample_close_signal = {
        "action": "close",
        "symbol": "BTCUSDT",
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    return jsonify({
        'success': True,
        'message': 'State-aware MA Cross webhook test endpoint ready',
        'webhook_url': '/binance/state-aware-ma-cross-webhook',
        'sample_formats': {
            'buy_signal': sample_buy_signal,
            'sell_signal': sample_sell_signal,
            'close_signal': sample_close_signal
        },
        'features': [
            'State-aware MA Cross strategy support',
            'Auto-calculated position sizing based on account balance',
            'Dual direction strategy (long and short positions)',
            'Closes opposite positions before opening new ones',
            'Buy signals for long entries, sell signals for short entries',
            'Close signals to exit all positions',
            'Supports both bullish and bearish market conditions',
            'Respects symbol precision and tick size',
            'Comprehensive order tracking and logging',
            'Balance percentage-based position sizing (default 20%)'
        ],
        'usage_instructions': {
            'step_1': 'Configure TradingView alert to send to /binance/state-aware-ma-cross-webhook or /tradingview/binancebinance/state-aware-ma-cross-webhook',
            'step_2': 'Set pine script alert message to the raw JSON format',
            'step_3': 'Ensure Binance API credentials are configured with futures trading permissions',
            'step_4': 'The webhook will automatically handle MA cross signals from your State-aware strategy'
        },
        'supported_urls': [
            '/api/binance/state-aware-ma-cross-webhook',
            '/api/tradingview/binancebinance/state-aware-ma-cross-webhook'
        ],
        'pine_script_integration': {
            'buy_alert_message': '{"action": "buy", "symbol": "' + '{{ticker}}' + '", "balance_percentage": "0.20", "leverage": "10", "entry": "' + '{{close}}' + '"}',
            'sell_alert_message': '{"action": "sell", "symbol": "' + '{{ticker}}' + '", "balance_percentage": "0.20", "leverage": "10", "entry": "' + '{{close}}' + '"}',
            'close_alert_message': '{"action": "close", "symbol": "' + '{{ticker}}' + '", "leverage": "10", "entry": "' + '{{close}}' + '"}',
            'balance_percentage_options': {
                '10%': '0.10',
                '20%': '0.20', 
                '30%': '0.30',
                '50%': '0.50'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@binance_bp.route('/binance/test', methods=['POST'])
def test_binance_connection():
    """Test Binance Futures connection and trading functionality"""
    global binance_client
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured'
        }), 400
    
    try:
        # Test futures connection
        server_time = call_binance_api(binance_client.get_server_time)
        futures_account = call_binance_api(binance_client.futures_account)
        
        # Get some futures market data
        btc_price = call_binance_api(binance_client.futures_symbol_ticker, symbol='BTCUSDT')
        
        # Get exchange info for futures
        exchange_info = call_binance_api(binance_client.futures_exchange_info)
        
        return jsonify({
            'success': True,
            'message': 'Binance Futures connection test successful',
            'server_time': server_time,
            'can_trade': futures_account.get('canTrade'),
            'can_deposit': futures_account.get('canDeposit'),
            'can_withdraw': futures_account.get('canWithdraw'),
            'total_wallet_balance': futures_account.get('totalWalletBalance'),
            'btc_price': btc_price['price'],
            'testnet': trading_config['testnet'],
            'leverage': trading_config['leverage'],
            'margin_type': trading_config['margin_type'],
            'active_symbols_count': len([s for s in exchange_info['symbols'] if s['status'] == 'TRADING']),
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Connection test error: {str(e)}'
        }), 500

@binance_bp.route('/binance/test-state-aware-close', methods=['POST'])
def test_state_aware_close_webhook():
    """Test the State-aware MA Cross webhook close functionality with sample data"""
    
    # Test data for close signal
    test_close_data = {
        'action': 'close',
        'symbol': 'BTCUSDT',
        'leverage': '10',
        'entry': '50000.00'
    }
    
    return jsonify({
        'success': True,
        'message': 'State-aware MA Cross close test data generated',
        'test_webhook_url': '/api/binance/state-aware-ma-cross-webhook',
        'alternative_url': '/api/tradingview/binancebinance/state-aware-ma-cross-webhook',
        'test_data': test_close_data,
        'features': [
            'Immediately closes ALL positions (both long and short) for the specified symbol',
            'Cancels any existing open orders for the symbol',
            'Works with any symbol supported by Binance Futures',
            'Provides detailed response with closed position information',
            'Tracks both long and short positions separately in response'
        ],
        'usage_note': 'Send the test_data as JSON POST to the webhook URL to test close functionality',
        'pine_script_close_message': '{"action": "close", "symbol": "{{ticker}}", "leverage": "10", "entry": "{{close}}"}',
        'timestamp': datetime.now().isoformat()
    })

