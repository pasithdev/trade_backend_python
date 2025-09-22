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

def init_binance_client(api_key, api_secret, testnet=True):
    """Initialize Binance client with API credentials for Futures trading"""
    global binance_client
    try:
        logger.info(f"Initializing Binance client (testnet: {testnet})")
        
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
            server_time = binance_client.get_server_time()
            logger.info(f"Server time test successful: {server_time}")
        except Exception as server_error:
            logger.error(f"Failed to get server time: {server_error}")
            raise Exception(f"Basic connection test failed: {server_error}")
        
        # Test the futures connection
        try:
            futures_account_info = binance_client.futures_account()
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
            binance_client.futures_change_position_mode(dualSidePosition=False)
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
        futures_account = binance_client.futures_account()
        
        # Get positions
        positions = binance_client.futures_position_information()
        
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
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
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
        symbol_info = binance_client.get_symbol_info(symbol)
        lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size_filter['stepSize'])
        quantity = round(quantity - (quantity % step_size), 8)
        
        if action == 'buy':
            # Place market buy order
            order = binance_client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            
            # Calculate TP and SL prices
            tp_price = current_price * (1 + tp_percentage / 100)
            sl_price = current_price * (1 - sl_percentage / 100)
            
            # Place OCO sell order for TP/SL
            oco_order = binance_client.create_oco_order(
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
            order = binance_client.order_market_sell(
                symbol=symbol,
                quantity=quantity
            )
            
            # For sell orders, TP is lower price, SL is higher price
            tp_price = current_price * (1 - tp_percentage / 100)
            sl_price = current_price * (1 + sl_percentage / 100)
            
            # Place OCO buy order for TP/SL
            oco_order = binance_client.create_oco_order(
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
        orders = binance_client.futures_get_open_orders(symbol=symbol)
        
        # Get position information
        positions = binance_client.futures_position_information(symbol=symbol)
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
        ticker = binance_client.futures_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        # Set leverage for the symbol
        try:
            binance_client.futures_change_leverage(symbol=symbol, leverage=trading_config['leverage'])
            logger.info(f"Leverage set to {trading_config['leverage']}x for {symbol}")
        except Exception as lev_error:
            logger.warning(f"Could not set leverage for {symbol}: {lev_error}")
        
        # Set margin type
        try:
            binance_client.futures_change_margin_type(symbol=symbol, marginType=trading_config['margin_type'])
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
        exchange_info = binance_client.futures_exchange_info()
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
        
        main_order = binance_client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        logger.info(f"Main order executed: {action} {quantity} {symbol}")
        
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
                    tp_order = binance_client.futures_create_order(
                        symbol=symbol,
                        side=close_side,
                        type='TAKE_PROFIT_MARKET',
                        quantity=quantity,
                        stopPrice=final_tp_price,
                        reduceOnly=True,
                        timeInForce='GTC'
                    )
                    logger.info(f"Take Profit order placed: {close_side} {quantity} at {final_tp_price}")
                except Exception as tp_error:
                    logger.error(f"Failed to place Take Profit order: {str(tp_error)}")
            
            # Place Stop Loss order
            if final_sl_price:
                try:
                    sl_order = binance_client.futures_create_order(
                        symbol=symbol,
                        side=close_side,
                        type='STOP_MARKET',
                        quantity=quantity,
                        stopPrice=final_sl_price,
                        reduceOnly=True,
                        timeInForce='GTC'
                    )
                    logger.info(f"Stop Loss order placed: {close_side} {quantity} at {final_sl_price}")
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
        server_time = binance_client.get_server_time()
        futures_account = binance_client.futures_account()
        
        # Get some futures market data
        btc_price = binance_client.futures_symbol_ticker(symbol='BTCUSDT')
        
        # Get exchange info for futures
        exchange_info = binance_client.futures_exchange_info()
        
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

