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

# Global variables for Binance client and configuration
binance_client = None
trading_config = {
    'testnet': True,  # Use testnet by default for safety
    'default_tp_percentage': 2.0,  # 2% take profit
    'default_sl_percentage': 1.0,  # 1% stop loss
    'min_order_value': 10.0,  # Minimum order value in USDT
    'max_order_value': 1000.0,  # Maximum order value in USDT
    'leverage': 10,  # Default leverage for futures trading
    'margin_type': 'ISOLATED',  # ISOLATED or CROSSED
    'position_side': 'BOTH'  # BOTH, LONG, or SHORT (for hedge mode)
}

# Store active orders for tracking
active_orders = []

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
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
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
            return {
                'success': False,
                'error': f'Calculated quantity {final_quantity} is below minimum {min_qty} for {symbol}',
                'details': {
                    'calculated_quantity': final_quantity,
                    'minimum_quantity': min_qty,
                    'position_value_usdt': position_value_usdt,
                    'current_price': current_price
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
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured. Please configure API credentials first.'
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
        
        # Step 1: Close opposite position first
        close_result = close_opposite_position(symbol, action)
        if not close_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to close existing position: {close_result["error"]}'
            }), 400
        
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
        
        # Step 5: Execute main entry order
        side = 'BUY' if action == 'buy' else 'SELL'
        
        main_order = call_binance_api(binance_client.futures_create_order,
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        logger.info(f"Main entry order executed: {action} {quantity} {symbol} (dual direction strategy)")
        
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
        
        return jsonify({
            'success': True,
            'message': f'Target Trend order executed: {action} {quantity} {symbol} (dual direction mode)',
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
                'opposite_position_closed': close_result.get('message', 'No opposite positions'),
                'mode': 'dual_direction',
                'quantity_calculation': quantity_result['details'],
                'note': f'Quantity calculated from {balance_percentage*100}% of account balance with {leverage}x leverage'
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
        "quantity": "0.20",
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    sample_sell_signal = {
        "action": "sell",
        "symbol": "BTCUSDT", 
        "quantity": "0.20",
        "leverage": "10",
        "entry": "50000.12345678"
    }
    
    return jsonify({
        'success': True,
        'message': 'Target Trend webhook test endpoint ready',
        'webhook_url': '/binance/target-trend-webhook',
        'sample_formats': {
            'buy_signal': sample_buy_signal,
            'sell_signal': sample_sell_signal
        },
        'features': [
            'Dual direction strategy (long and short positions)',
            'Closes opposite positions before opening new ones',
            'Buy signals for long entries, sell signals for short entries',
            'Supports both bullish and bearish market conditions',
            'Respects symbol precision and tick size',
            'Comprehensive order tracking and logging',
            'Simplified JSON format'
        ],
        'usage_instructions': {
            'step_1': 'Configure TradingView alert to send to /binance/target-trend-webhook or /tradingview/binancebinance/target-trend-webhook',
            'step_2': 'Set pine script alert message to the raw JSON format',
            'step_3': 'Ensure Binance API credentials are configured with futures trading permissions'
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
    
    if not binance_client:
        return jsonify({
            'success': False,
            'error': 'Binance client not configured. Please configure API credentials first.'
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
            return jsonify({
                'success': False,
                'error': f'Failed to calculate position quantity: {quantity_result["error"]}',
                'details': quantity_result['details']
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
        logger.error(f"Binance API error in State-aware MA Cross webhook: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Binance API error: {e.message}'
        }), 400
    except BinanceOrderException as e:
        logger.error(f"Binance order error in State-aware MA Cross webhook: {e.message}")
        return jsonify({
            'success': False,
            'error': f'Order error: {e.message}'
        }), 400
    except Exception as e:
        logger.error(f"Error in State-aware MA Cross webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'State-aware MA Cross webhook error: {str(e)}'
        }), 500

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

