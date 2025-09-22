from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime
import logging
from .binance_trading import execute_tradingview_trade

tradingview_bp = Blueprint('tradingview', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store received alerts
received_alerts = []

# Configuration for automatic trading
auto_trading_config = {
    'enabled': False,  # Disabled by default for safety
    'require_tp_sl': True,  # Require both TP and SL for automatic trades
    'max_daily_trades': 10,  # Maximum number of automatic trades per day
    'daily_trade_count': 0,  # Current daily trade count
    'last_reset_date': None
}

# Configuration for MT4 integration
mt4_config = {
    'enabled': False,  # MT4 integration disabled by default
    'signals_directory': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mt4_signals'),
    'max_signal_age': 300,  # Maximum age of signal files in seconds (5 minutes)
    'currency_pairs': {
        # Crypto to Forex conversion mapping
        'BTCUSD': 'BTCUSD',
        'EURUSD': 'EURUSD', 
        'GBPUSD': 'GBPUSD',
        'USDJPY': 'USDJPY',
        'USDCHF': 'USDCHF',
        'AUDUSD': 'AUDUSD',
        'USDCAD': 'USDCAD',
        'NZDUSD': 'NZDUSD',
        'EURJPY': 'EURJPY',
        'GBPJPY': 'GBPJPY',
        'EURGBP': 'EURGBP',
        'XAUUSD': 'GOLD',  # Gold
        'XAGUSD': 'SILVER',  # Silver
        'US30': 'US30',  # Dow Jones
        'SPX500': 'SPX500',  # S&P 500
        'NAS100': 'NAS100'  # Nasdaq
    },
    'default_lot_size': 0.01,
    'max_lot_size': 1.0,
    'magic_number': 123456
}

def normalize_tradingview_data(data):
    """
    Normalize TradingView data to standard format
    Handles both old format (action, price) and new format (alert_type, entry_price)
    """
    normalized = data.copy()
    
    # Handle alert_type -> action mapping
    if 'alert_type' in data:
        alert_type = data['alert_type'].upper()
        if alert_type in ['BUY', 'LONG']:
            normalized['action'] = 'buy'
        elif alert_type in ['SELL', 'SHORT']:
            normalized['action'] = 'sell'
        else:
            normalized['action'] = data.get('action', 'unknown')
    
    # Handle entry_price -> price mapping
    if 'entry_price' in data and 'price' not in data:
        normalized['price'] = data['entry_price']
    
    # Preserve original fields for reference
    normalized['original_alert_type'] = data.get('alert_type')
    normalized['name_of_strategy'] = data.get('name_of_strategy')
    normalized['signal'] = data.get('signal')
    normalized['entry_price'] = data.get('entry_price')
    
    return normalized

def validate_webhook_data(data):
    """
    Validate webhook data for trading operations
    Supports both old and new TradingView parameter formats
    """
    errors = []
    
    # Get logger for this module
    validation_logger = logging.getLogger(__name__)
    
    # Normalize the data first
    normalized_data = normalize_tradingview_data(data)
    
    # Check required fields
    if not normalized_data.get('symbol'):
        errors.append("Missing required field: symbol")
    
    # Check action/alert_type
    action = normalized_data.get('action', '').lower()
    if not action or action not in ['buy', 'sell']:
        if data.get('alert_type'):
            errors.append("Invalid alert_type field (must be 'BUY', 'SELL', 'LONG', or 'SHORT')")
        else:
            errors.append("Missing or invalid action field (must be 'buy' or 'sell')")
    
    # Validate price (use normalized data)
    price_field = normalized_data.get('price') or normalized_data.get('entry_price')
    if price_field is not None:
        try:
            price = float(price_field)
            if price <= 0:
                errors.append("Entry price must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Invalid entry price format")
    
    # Validate take profit
    if data.get('tp') is not None:
        try:
            tp = float(data.get('tp'))
            if tp <= 0:
                errors.append("Take profit must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Invalid take profit format")
    
    # Validate stop loss
    if data.get('sl') is not None:
        try:
            sl = float(data.get('sl'))
            if sl <= 0:
                errors.append("Stop loss must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Invalid stop loss format")
    
    # Validate quantity
    if data.get('quantity') is not None:
        try:
            quantity = float(data.get('quantity'))
            if quantity <= 0:
                errors.append("Quantity must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Invalid quantity format")
    
    # Log TP/SL logic for informational purposes (but don't enforce as errors)
    if (action == 'buy' and price_field and data.get('tp') and data.get('sl')):
        try:
            price = float(price_field)
            tp = float(data.get('tp'))
            sl = float(data.get('sl'))
            
            # Just log warnings, don't add as validation errors
            if tp <= price:
                validation_logger.info(f"Note: For buy order, TP ({tp}) is not higher than entry price ({price})")
            if sl >= price:
                validation_logger.info(f"Note: For buy order, SL ({sl}) is not lower than entry price ({price})")
        except (ValueError, TypeError):
            pass  # Already handled above
    
    # Log TP/SL logic for sell orders (informational only)
    if (action == 'sell' and price_field and data.get('tp') and data.get('sl')):
        try:
            price = float(price_field)
            tp = float(data.get('tp'))
            sl = float(data.get('sl'))
            
            # Just log warnings, don't add as validation errors
            if tp >= price:
                validation_logger.info(f"Note: For sell order, TP ({tp}) is not lower than entry price ({price})")
            if sl <= price:
                validation_logger.info(f"Note: For sell order, SL ({sl}) is not higher than entry price ({price})")
        except (ValueError, TypeError):
            pass  # Already handled above
    
    return errors

def convert_symbol_for_forex(symbol):
    """
    Convert TradingView symbol to forex broker compatible symbol
    """
    symbol = symbol.upper()
    
    # Remove common suffixes
    symbol = symbol.replace('USD', '').replace('USDT', '')
    
    # Check if it's in our mapping
    if symbol + 'USD' in mt4_config['currency_pairs']:
        return mt4_config['currency_pairs'][symbol + 'USD']
    elif symbol in mt4_config['currency_pairs']:
        return mt4_config['currency_pairs'][symbol]
    
    # Default conversions for common forex pairs
    forex_conversions = {
        'EUR': 'EURUSD',
        'GBP': 'GBPUSD', 
        'JPY': 'USDJPY',
        'CHF': 'USDCHF',
        'AUD': 'AUDUSD',
        'CAD': 'USDCAD',
        'NZD': 'NZDUSD',
        'BTC': 'BTCUSD',
        'ETH': 'ETHUSD',
        'XAU': 'GOLD',
        'GOLD': 'GOLD',
        'XAG': 'SILVER',
        'SILVER': 'SILVER'
    }
    
    return forex_conversions.get(symbol, symbol + 'USD')

def write_signal_to_mt4(signal_data, is_mt4_only_webhook=False):
    """
    Write trading signal to file for MT4 EA to read
    """
    try:
        # Ensure signals directory exists
        os.makedirs(mt4_config['signals_directory'], exist_ok=True)
        
        # Normalize the data to handle both old and new formats
        normalized_data = normalize_tradingview_data(signal_data)
        
        # Convert symbol to forex format
        original_symbol = normalized_data.get('symbol', '')
        forex_symbol = convert_symbol_for_forex(original_symbol)
        
        # Determine lot size based on webhook type and parameters
        if is_mt4_only_webhook:
            # For MT4-only webhook, always use EA's default lot size (ignore quantity)
            lot_size = mt4_config['default_lot_size']
            logger.info(f"MT4-only webhook: Using EA default lot size {lot_size} (ignoring quantity parameter)")
        else:
            # For combined webhook, use quantity if provided, otherwise default
            quantity = normalized_data.get('quantity')
            if quantity:
                lot_size = min(float(quantity), mt4_config['max_lot_size'])
            else:
                lot_size = mt4_config['default_lot_size']
        
        # Prepare signal data for MT4
        mt4_signal = {
            'timestamp': datetime.now().isoformat(),
            'symbol': forex_symbol,
            'original_symbol': original_symbol,
            'action': normalized_data.get('action', '').upper(),  # BUY or SELL
            'entry_price': normalized_data.get('price', 0) or normalized_data.get('entry_price', 0),
            'tp_price': normalized_data.get('tp', 0),
            'sl_price': normalized_data.get('sl', 0),
            'lot_size': lot_size,
            'magic_number': mt4_config['magic_number'],
            'message': normalized_data.get('message', ''),
            'processed': False,
            # Include original TradingView fields for reference
            'original_alert_type': normalized_data.get('original_alert_type'),
            'name_of_strategy': normalized_data.get('name_of_strategy'),
            'signal': normalized_data.get('signal'),
            'webhook_type': 'mt4_only' if is_mt4_only_webhook else 'combined'
        }
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"signal_{timestamp}_{forex_symbol}_{mt4_signal['action']}.json"
        filepath = os.path.join(mt4_config['signals_directory'], filename)
        
        # Write signal file
        with open(filepath, 'w') as f:
            json.dump(mt4_signal, f, indent=2)
        
        logger.info(f"MT4 signal written: {filepath}")
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'signal': mt4_signal
        }
        
    except Exception as e:
        logger.error(f"Failed to write MT4 signal: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_old_signals():
    """
    Clean up old signal files to prevent directory buildup
    """
    try:
        if not os.path.exists(mt4_config['signals_directory']):
            return
        
        current_time = datetime.now()
        cleaned_count = 0
        
        for filename in os.listdir(mt4_config['signals_directory']):
            filepath = os.path.join(mt4_config['signals_directory'], filename)
            
            if filename.endswith('.json'):
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    age_seconds = (current_time - file_time).total_seconds()
                    
                    if age_seconds > mt4_config['max_signal_age']:
                        os.remove(filepath)
                        cleaned_count += 1
                        logger.debug(f"Cleaned old signal file: {filename}")
                        
                except Exception as file_error:
                    logger.warning(f"Error processing signal file {filename}: {file_error}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} old signal files")
            
    except Exception as e:
        logger.error(f"Error during signal cleanup: {str(e)}")

@tradingview_bp.route('/tradingview/webhook', methods=['POST'])
def receive_tradingview_webhook():
    """
    Receive webhook alerts from TradingView
    Expected payload format:
    {
        "symbol": "BTCUSD",
        "action": "buy" or "sell",
        "price": 50000.00,
        "tp": 52000.00,
        "sl": 48000.00,
        "quantity": 0.001,
        "message": "Custom alert message"
    }
    """
    global received_alerts
    
    try:
        # Get the content type
        content_type = request.headers.get('Content-Type', '')
        
        # Parse the request data based on content type
        if 'application/json' in content_type:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON payload'
                }), 400
        else:
            # Handle plain text payload
            raw_data = request.get_data(as_text=True)
            try:
                # Try to parse as JSON first
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text message
                data = {'message': raw_data}
        
        # Add timestamp and source info
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'tradingview',
            'raw_data': data,
            'processed': False
        }
        
        # Try to extract standard fields
        if isinstance(data, dict):
            # Normalize and validate the data
            normalized_data = normalize_tradingview_data(data)
            validation_errors = validate_webhook_data(data)
            
            alert_data.update({
                'symbol': normalized_data.get('symbol', 'UNKNOWN'),
                'action': normalized_data.get('action', 'unknown'),
                'price': normalized_data.get('price') or normalized_data.get('entry_price'),
                'tp': normalized_data.get('tp'),  # Take Profit
                'sl': normalized_data.get('sl'),  # Stop Loss
                'quantity': normalized_data.get('quantity'),
                'message': normalized_data.get('message', str(data)),
                'validation_errors': validation_errors,
                'is_valid': len(validation_errors) == 0,
                # Include new TradingView fields
                'alert_type': normalized_data.get('original_alert_type'),
                'name_of_strategy': normalized_data.get('name_of_strategy'),
                'signal': normalized_data.get('signal'),
                'entry_price': normalized_data.get('entry_price')
            })
            
            # Log validation errors
            if validation_errors:
                logger.warning(f"Webhook validation errors: {validation_errors}")
        else:
            alert_data.update({
                'symbol': 'UNKNOWN',
                'action': 'unknown',
                'price': None,
                'tp': None,
                'sl': None,
                'quantity': None,
                'message': str(data),
                'validation_errors': ['Invalid data format'],
                'is_valid': False,
                'alert_type': None,
                'name_of_strategy': None,
                'signal': None,
                'entry_price': None
            })
        
        # Store the alert (trade result will be added after execution)
        received_alerts.append(alert_data)
        
        # Keep only the last 100 alerts
        if len(received_alerts) > 100:
            received_alerts = received_alerts[-100:]
        
        # Log the received alert
        logger.info(f"Received TradingView alert: {alert_data}")
        
        # Check if automatic trading is enabled and perform safety checks
        trade_result = None
        should_execute_trade = False
        
        # Check if automatic trading is enabled
        if not auto_trading_config['enabled']:
            trade_result = {
                'success': False,
                'error': 'Automatic trading is disabled. Enable it first to execute trades.',
                'trade_executed': False
            }
        elif not alert_data.get('is_valid', False):
            logger.warning("Alert validation failed, skipping automatic trade execution")
            trade_result = {
                'success': False,
                'error': 'Alert validation failed',
                'trade_executed': False
            }
        else:
            # Reset daily counter if new day
            from datetime import date
            today = date.today().isoformat()
            if auto_trading_config['last_reset_date'] != today:
                auto_trading_config['daily_trade_count'] = 0
                auto_trading_config['last_reset_date'] = today
            
            # Check daily trade limit
            if auto_trading_config['daily_trade_count'] >= auto_trading_config['max_daily_trades']:
                trade_result = {
                    'success': False,
                    'error': f'Daily trade limit reached ({auto_trading_config["max_daily_trades"]} trades)',
                    'trade_executed': False
                }
            # Check if TP/SL required (only check for presence, not logic)
            elif (auto_trading_config['require_tp_sl'] and 
                  (not alert_data.get('tp') or not alert_data.get('sl'))):
                trade_result = {
                    'success': False,
                    'error': 'Take Profit and Stop Loss values are required for automatic trading',
                    'trade_executed': False
                }
            else:
                should_execute_trade = True
        
        # Execute trade if all checks pass
        if should_execute_trade:
            logger.info("All safety checks passed, executing automatic trade on Binance...")
            try:
                trade_result = execute_tradingview_trade(alert_data)
                logger.info(f"Trade execution result: {trade_result}")
                
                # Increment daily trade counter if trade was successful
                if trade_result.get('trade_executed'):
                    auto_trading_config['daily_trade_count'] += 1
                    logger.info(f"Daily trade count: {auto_trading_config['daily_trade_count']}/{auto_trading_config['max_daily_trades']}")
                    
            except Exception as trade_error:
                logger.error(f"Error executing automatic trade: {str(trade_error)}")
                trade_result = {
                    'success': False,
                    'error': f'Trade execution failed: {str(trade_error)}',
                    'trade_executed': False
                }
        
        # Store trade result in alert data
        alert_data['trade_result'] = trade_result
        
        # Send signal to MT4 if enabled
        mt4_result = None
        if mt4_config['enabled'] and alert_data.get('is_valid', False):
            logger.info("MT4 integration enabled, sending signal to MT4...")
            try:
                # Cleanup old signals first
                cleanup_old_signals()
                
                # Write signal for MT4 (combined webhook)
                mt4_result = write_signal_to_mt4(alert_data, is_mt4_only_webhook=False)
                logger.info(f"MT4 signal result: {mt4_result}")
            except Exception as mt4_error:
                logger.error(f"Error sending signal to MT4: {str(mt4_error)}")
                mt4_result = {
                    'success': False,
                    'error': f'MT4 signal failed: {str(mt4_error)}'
                }
        elif mt4_config['enabled']:
            logger.warning("MT4 enabled but alert validation failed, skipping MT4 signal")
            mt4_result = {
                'success': False,
                'error': 'Alert validation failed, MT4 signal skipped'
            }
        
        # Store MT4 result in alert data
        alert_data['mt4_result'] = mt4_result
        
        response = {
            'success': True,
            'message': 'Alert received successfully',
            'alert_id': len(received_alerts),
            'timestamp': alert_data['timestamp'],
            'is_valid': alert_data.get('is_valid', False),
            'trade_executed': trade_result.get('trade_executed', False) if trade_result else False,
            'mt4_signal_sent': mt4_result.get('success', False) if mt4_result else False
        }
        
        # Include validation errors in response if any
        if alert_data.get('validation_errors'):
            response['validation_errors'] = alert_data['validation_errors']
            response['message'] = 'Alert received with validation warnings'
        
        # Include trade execution result
        if trade_result:
            response['trade_result'] = trade_result
        
        # Include MT4 result
        if mt4_result:
            response['mt4_result'] = mt4_result
        
        # Update message based on results
        success_messages = []
        if trade_result and trade_result.get('trade_executed'):
            success_messages.append('Binance trade executed')
        if mt4_result and mt4_result.get('success'):
            success_messages.append('MT4 signal sent')
        
        if success_messages:
            response['message'] = f"Alert received and {', '.join(success_messages)} successfully"
        elif not alert_data.get('is_valid', False):
            response['message'] = 'Alert received but failed validation - no trades executed'
        else:
            response['message'] = 'Alert received but execution failed'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing TradingView webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/alerts', methods=['GET'])
def get_received_alerts():
    """
    Get all received TradingView alerts
    """
    global received_alerts
    
    # Get query parameters for filtering
    limit = request.args.get('limit', 50, type=int)
    symbol = request.args.get('symbol')
    action = request.args.get('action')
    
    # Filter alerts if parameters provided
    filtered_alerts = received_alerts
    
    if symbol:
        filtered_alerts = [alert for alert in filtered_alerts if alert.get('symbol', '').upper() == symbol.upper()]
    
    if action:
        filtered_alerts = [alert for alert in filtered_alerts if alert.get('action', '').lower() == action.lower()]
    
    # Apply limit
    filtered_alerts = filtered_alerts[-limit:]
    
    return jsonify({
        'success': True,
        'alerts': filtered_alerts,
        'total_count': len(received_alerts),
        'filtered_count': len(filtered_alerts),
        'timestamp': datetime.now().isoformat()
    })

@tradingview_bp.route('/tradingview/alerts/<int:alert_id>', methods=['GET'])
def get_alert_by_id(alert_id):
    """
    Get a specific alert by ID
    """
    global received_alerts
    
    if alert_id < 1 or alert_id > len(received_alerts):
        return jsonify({
            'success': False,
            'error': 'Alert not found'
        }), 404
    
    alert = received_alerts[alert_id - 1]
    
    return jsonify({
        'success': True,
        'alert': alert,
        'timestamp': datetime.now().isoformat()
    })

@tradingview_bp.route('/tradingview/alerts', methods=['DELETE'])
def clear_alerts():
    """
    Clear all received alerts
    """
    global received_alerts
    
    count = len(received_alerts)
    received_alerts = []
    
    return jsonify({
        'success': True,
        'message': f'Cleared {count} alerts',
        'timestamp': datetime.now().isoformat()
    })

@tradingview_bp.route('/tradingview/test', methods=['POST'])
def test_webhook():
    """
    Test endpoint for webhook functionality
    """
    try:
        data = request.get_json() or {}
        
        test_alert = {
            'timestamp': datetime.now().isoformat(),
            'source': 'test',
            'symbol': data.get('symbol', 'BTCUSD'),
            'action': data.get('action', 'buy'),
            'price': data.get('price', 50000.00),
            'tp': data.get('tp', 52000.00),  # Take Profit
            'sl': data.get('sl', 48000.00),  # Stop Loss
            'quantity': data.get('quantity', 0.001),
            'message': data.get('message', 'Test alert'),
            'raw_data': data,
            'processed': False
        }
        
        received_alerts.append(test_alert)
        
        logger.info(f"Test alert created: {test_alert}")
        
        return jsonify({
            'success': True,
            'message': 'Test alert created successfully',
            'alert': test_alert
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error creating test alert: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/auto-trading/config', methods=['POST'])
def configure_auto_trading():
    """
    Configure automatic trading settings for TradingView webhooks
    """
    global auto_trading_config
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing configuration data'
            }), 400
        
        # Update configuration
        if 'enabled' in data:
            auto_trading_config['enabled'] = bool(data['enabled'])
            logger.info(f"Automatic trading {'enabled' if data['enabled'] else 'disabled'}")
        
        if 'require_tp_sl' in data:
            auto_trading_config['require_tp_sl'] = bool(data['require_tp_sl'])
        
        if 'max_daily_trades' in data:
            max_trades = int(data['max_daily_trades'])
            if max_trades < 1 or max_trades > 100:
                return jsonify({
                    'success': False,
                    'error': 'max_daily_trades must be between 1 and 100'
                }), 400
            auto_trading_config['max_daily_trades'] = max_trades
        
        return jsonify({
            'success': True,
            'message': 'Auto-trading configuration updated successfully',
            'config': {
                'enabled': auto_trading_config['enabled'],
                'require_tp_sl': auto_trading_config['require_tp_sl'],
                'max_daily_trades': auto_trading_config['max_daily_trades'],
                'daily_trade_count': auto_trading_config['daily_trade_count'],
                'last_reset_date': auto_trading_config['last_reset_date']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/auto-trading/config', methods=['GET'])
def get_auto_trading_config():
    """
    Get current automatic trading configuration
    """
    global auto_trading_config
    
    return jsonify({
        'success': True,
        'config': {
            'enabled': auto_trading_config['enabled'],
            'require_tp_sl': auto_trading_config['require_tp_sl'],
            'max_daily_trades': auto_trading_config['max_daily_trades'],
            'daily_trade_count': auto_trading_config['daily_trade_count'],
            'last_reset_date': auto_trading_config['last_reset_date']
        },
        'timestamp': datetime.now().isoformat()
    })

@tradingview_bp.route('/tradingview/mt4/config', methods=['POST'])
def configure_mt4():
    """
    Configure MT4 integration settings for TradingView webhooks
    """
    global mt4_config
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing configuration data'
            }), 400
        
        # Update configuration
        if 'enabled' in data:
            mt4_config['enabled'] = bool(data['enabled'])
            logger.info(f"MT4 integration {'enabled' if data['enabled'] else 'disabled'}")
        
        if 'signals_directory' in data:
            mt4_config['signals_directory'] = str(data['signals_directory'])
        
        if 'default_lot_size' in data:
            lot_size = float(data['default_lot_size'])
            if lot_size <= 0 or lot_size > mt4_config['max_lot_size']:
                return jsonify({
                    'success': False,
                    'error': f'Default lot size must be between 0 and {mt4_config["max_lot_size"]}'
                }), 400
            mt4_config['default_lot_size'] = lot_size
        
        if 'max_lot_size' in data:
            max_lot = float(data['max_lot_size'])
            if max_lot <= 0 or max_lot > 100:
                return jsonify({
                    'success': False,
                    'error': 'Max lot size must be between 0 and 100'
                }), 400
            mt4_config['max_lot_size'] = max_lot
        
        if 'magic_number' in data:
            magic = int(data['magic_number'])
            if magic < 0 or magic > 2147483647:
                return jsonify({
                    'success': False,
                    'error': 'Magic number must be between 0 and 2147483647'
                }), 400
            mt4_config['magic_number'] = magic
        
        if 'max_signal_age' in data:
            age = int(data['max_signal_age'])
            if age < 60 or age > 3600:
                return jsonify({
                    'success': False,
                    'error': 'Max signal age must be between 60 and 3600 seconds'
                }), 400
            mt4_config['max_signal_age'] = age
        
        # Update currency pair mappings if provided
        if 'currency_pairs' in data and isinstance(data['currency_pairs'], dict):
            mt4_config['currency_pairs'].update(data['currency_pairs'])
        
        # Ensure signals directory exists if MT4 is enabled
        if mt4_config['enabled']:
            try:
                os.makedirs(mt4_config['signals_directory'], exist_ok=True)
                logger.info(f"MT4 signals directory ready: {mt4_config['signals_directory']}")
            except Exception as dir_error:
                return jsonify({
                    'success': False,
                    'error': f'Cannot create signals directory: {str(dir_error)}'
                }), 400
        
        return jsonify({
            'success': True,
            'message': 'MT4 configuration updated successfully',
            'config': {
                'enabled': mt4_config['enabled'],
                'signals_directory': mt4_config['signals_directory'],
                'default_lot_size': mt4_config['default_lot_size'],
                'max_lot_size': mt4_config['max_lot_size'],
                'magic_number': mt4_config['magic_number'],
                'max_signal_age': mt4_config['max_signal_age'],
                'currency_pairs_count': len(mt4_config['currency_pairs'])
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'MT4 configuration error: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/mt4/config', methods=['GET'])
def get_mt4_config():
    """
    Get current MT4 integration configuration
    """
    global mt4_config
    
    # Check if signals directory exists and is accessible
    directory_status = 'not_exists'
    if os.path.exists(mt4_config['signals_directory']):
        if os.access(mt4_config['signals_directory'], os.R_OK | os.W_OK):
            directory_status = 'accessible'
        else:
            directory_status = 'not_accessible'
    
    # Count existing signal files
    signal_files_count = 0
    if os.path.exists(mt4_config['signals_directory']):
        try:
            signal_files_count = len([f for f in os.listdir(mt4_config['signals_directory']) if f.endswith('.json')])
        except:
            pass
    
    return jsonify({
        'success': True,
        'config': {
            'enabled': mt4_config['enabled'],
            'signals_directory': mt4_config['signals_directory'],
            'default_lot_size': mt4_config['default_lot_size'],
            'max_lot_size': mt4_config['max_lot_size'],
            'magic_number': mt4_config['magic_number'],
            'max_signal_age': mt4_config['max_signal_age'],
            'currency_pairs': mt4_config['currency_pairs']
        },
        'status': {
            'directory_status': directory_status,
            'signal_files_count': signal_files_count
        },
        'timestamp': datetime.now().isoformat()
    })

@tradingview_bp.route('/tradingview/mt4/test-signal', methods=['POST'])
def test_mt4_signal():
    """
    Test MT4 signal generation with sample data
    """
    try:
        data = request.get_json() or {}
        
        # Create test signal data (supports both old and new formats)
        test_signal = {
            'symbol': data.get('symbol', 'EURUSD'),
            'action': data.get('action', 'buy'),
            'alert_type': data.get('alert_type', 'BUY'),
            'name_of_strategy': data.get('name_of_strategy', 'TestStrategy'),
            'signal': data.get('signal', 'LONG'),
            'price': data.get('price', 1.1000),
            'entry_price': data.get('entry_price', 1.1000),
            'tp': data.get('tp', 1.1020),
            'sl': data.get('sl', 1.0980),
            'quantity': data.get('quantity', mt4_config['default_lot_size']),
            'message': data.get('message', 'Test signal from TradingView webhook')
        }
        
        if not mt4_config['enabled']:
            return jsonify({
                'success': False,
                'error': 'MT4 integration is disabled. Enable it first.'
            }), 400
        
        # Clean up old signals
        cleanup_old_signals()
        
        # Write test signal (using MT4-only mode for test)
        result = write_signal_to_mt4(test_signal, is_mt4_only_webhook=True)
        
        return jsonify({
            'success': True,
            'message': 'Test signal generated successfully',
            'test_signal': test_signal,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Test signal error: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/mt4/webhook', methods=['POST'])
def receive_tradingview_mt4_webhook():
    """
    Dedicated webhook endpoint for TradingView to MT4 integration
    This endpoint only handles MT4 signals and doesn't execute Binance trades
    """
    global received_alerts, mt4_config
    
    try:
        # Get the content type
        content_type = request.headers.get('Content-Type', '')
        
        # Parse the request data based on content type
        if 'application/json' in content_type:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON payload'
                }), 400
        else:
            # Handle plain text payload
            raw_data = request.get_data(as_text=True)
            try:
                # Try to parse as JSON first
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text message
                data = {'message': raw_data}
        
        # Add timestamp and source info
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'tradingview_mt4_webhook',
            'raw_data': data,
            'processed': False,
            'endpoint': 'mt4_only'
        }
        
        # Try to extract standard fields
        if isinstance(data, dict):
            # Normalize and validate the data
            normalized_data = normalize_tradingview_data(data)
            validation_errors = validate_webhook_data(data)
            
            alert_data.update({
                'symbol': normalized_data.get('symbol', 'UNKNOWN'),
                'action': normalized_data.get('action', 'unknown'),
                'price': normalized_data.get('price') or normalized_data.get('entry_price'),
                'tp': normalized_data.get('tp'),  # Take Profit
                'sl': normalized_data.get('sl'),  # Stop Loss
                'quantity': normalized_data.get('quantity'),  # Will be ignored for MT4-only
                'message': normalized_data.get('message', str(data)),
                'validation_errors': validation_errors,
                'is_valid': len(validation_errors) == 0,
                # Include new TradingView fields
                'alert_type': normalized_data.get('original_alert_type'),
                'name_of_strategy': normalized_data.get('name_of_strategy'),
                'signal': normalized_data.get('signal'),
                'entry_price': normalized_data.get('entry_price')
            })
            
            # Log validation errors
            if validation_errors:
                logger.warning(f"MT4 Webhook validation errors: {validation_errors}")
        else:
            alert_data.update({
                'symbol': 'UNKNOWN',
                'action': 'unknown',
                'price': None,
                'tp': None,
                'sl': None,
                'quantity': None,
                'message': str(data),
                'validation_errors': ['Invalid data format'],
                'is_valid': False,
                'alert_type': None,
                'name_of_strategy': None,
                'signal': None,
                'entry_price': None
            })
        
        # Store the alert (for tracking purposes)
        received_alerts.append(alert_data)
        
        # Keep only the last 100 alerts
        if len(received_alerts) > 100:
            received_alerts = received_alerts[-100:]
        
        # Log the received alert
        logger.info(f"Received TradingView MT4 webhook alert: {alert_data}")
        
        # Send signal to MT4 if enabled and valid
        mt4_result = None
        if not mt4_config['enabled']:
            mt4_result = {
                'success': False,
                'error': 'MT4 integration is disabled. Enable it first to receive signals.',
                'signal_sent': False
            }
        elif not alert_data.get('is_valid', False):
            logger.warning("Alert validation failed, skipping MT4 signal")
            mt4_result = {
                'success': False,
                'error': 'Alert validation failed',
                'signal_sent': False
            }
        else:
            logger.info("Sending signal to MT4...")
            try:
                # Cleanup old signals first
                cleanup_old_signals()
                
                # Write signal for MT4 (MT4-only webhook)
                mt4_result = write_signal_to_mt4(alert_data, is_mt4_only_webhook=True)
                mt4_result['signal_sent'] = mt4_result.get('success', False)
                logger.info(f"MT4 signal result: {mt4_result}")
            except Exception as mt4_error:
                logger.error(f"Error sending signal to MT4: {str(mt4_error)}")
                mt4_result = {
                    'success': False,
                    'error': f'MT4 signal failed: {str(mt4_error)}',
                    'signal_sent': False
                }
        
        # Store MT4 result in alert data
        alert_data['mt4_result'] = mt4_result
        
        # Prepare response
        response = {
            'success': True,
            'message': 'MT4 webhook alert received successfully',
            'alert_id': len(received_alerts),
            'timestamp': alert_data['timestamp'],
            'is_valid': alert_data.get('is_valid', False),
            'mt4_signal_sent': mt4_result.get('signal_sent', False) if mt4_result else False
        }
        
        # Include validation errors in response if any
        if alert_data.get('validation_errors'):
            response['validation_errors'] = alert_data['validation_errors']
            response['message'] = 'MT4 webhook alert received with validation warnings'
        
        # Include MT4 result
        if mt4_result:
            response['mt4_result'] = mt4_result
        
        # Update message based on result
        if mt4_result and mt4_result.get('signal_sent'):
            response['message'] = 'Alert received and MT4 signal sent successfully'
        elif not alert_data.get('is_valid', False):
            response['message'] = 'Alert received but failed validation - no MT4 signal sent'
        elif not mt4_config['enabled']:
            response['message'] = 'Alert received but MT4 integration is disabled'
        else:
            response['message'] = 'Alert received but MT4 signal failed'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing TradingView MT4 webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'MT4 webhook error: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/binance/webhook', methods=['POST'])
def receive_tradingview_binance_webhook():
    """
    Dedicated webhook endpoint for TradingView to Binance integration
    This endpoint only handles Binance futures trades and doesn't send MT4 signals
    """
    global received_alerts, auto_trading_config
    
    try:
        # Get the content type
        content_type = request.headers.get('Content-Type', '')
        
        # Parse the request data based on content type
        if 'application/json' in content_type:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON payload'
                }), 400
        else:
            # Handle plain text payload
            raw_data = request.get_data(as_text=True)
            try:
                # Try to parse as JSON first
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text message
                data = {'message': raw_data}
        
        # Add timestamp and source info
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'tradingview_binance_webhook',
            'raw_data': data,
            'processed': False,
            'endpoint': 'binance_only'
        }
        
        # Try to extract standard fields
        if isinstance(data, dict):
            # Normalize and validate the data
            normalized_data = normalize_tradingview_data(data)
            validation_errors = validate_webhook_data(data)
            
            alert_data.update({
                'symbol': normalized_data.get('symbol', 'UNKNOWN'),
                'action': normalized_data.get('action', 'unknown'),
                'price': normalized_data.get('price') or normalized_data.get('entry_price'),
                'tp': normalized_data.get('tp'),  # Take Profit
                'sl': normalized_data.get('sl'),  # Stop Loss
                'quantity': normalized_data.get('quantity'),
                'message': normalized_data.get('message', str(data)),
                'validation_errors': validation_errors,
                'is_valid': len(validation_errors) == 0,
                # Include new TradingView fields
                'alert_type': normalized_data.get('original_alert_type'),
                'name_of_strategy': normalized_data.get('name_of_strategy'),
                'signal': normalized_data.get('signal'),
                'entry_price': normalized_data.get('entry_price')
            })
            
            # Log validation errors
            if validation_errors:
                logger.warning(f"Binance Webhook validation errors: {validation_errors}")
        else:
            alert_data.update({
                'symbol': 'UNKNOWN',
                'action': 'unknown',
                'price': None,
                'tp': None,
                'sl': None,
                'quantity': None,
                'message': str(data),
                'validation_errors': ['Invalid data format'],
                'is_valid': False,
                'alert_type': None,
                'name_of_strategy': None,
                'signal': None,
                'entry_price': None
            })
        
        # Store the alert (for tracking purposes)
        received_alerts.append(alert_data)
        
        # Keep only the last 100 alerts
        if len(received_alerts) > 100:
            received_alerts = received_alerts[-100:]
        
        # Log the received alert
        logger.info(f"Received TradingView Binance webhook alert: {alert_data}")
        
        # Check if automatic trading is enabled and perform safety checks
        trade_result = None
        should_execute_trade = False
        
        # Check if automatic trading is enabled
        if not auto_trading_config['enabled']:
            trade_result = {
                'success': False,
                'error': 'Automatic trading is disabled. Enable it first to execute trades.',
                'trade_executed': False
            }
        elif not alert_data.get('is_valid', False):
            logger.warning("Alert validation failed, skipping automatic trade execution")
            trade_result = {
                'success': False,
                'error': 'Alert validation failed',
                'trade_executed': False
            }
        else:
            # Reset daily counter if new day
            from datetime import date
            today = date.today().isoformat()
            if auto_trading_config['last_reset_date'] != today:
                auto_trading_config['daily_trade_count'] = 0
                auto_trading_config['last_reset_date'] = today
            
            # Check daily trade limit
            if auto_trading_config['daily_trade_count'] >= auto_trading_config['max_daily_trades']:
                trade_result = {
                    'success': False,
                    'error': f'Daily trade limit reached ({auto_trading_config["max_daily_trades"]} trades)',
                    'trade_executed': False
                }
            # Check if TP/SL required (only check for presence, not logic)
            elif (auto_trading_config['require_tp_sl'] and 
                  (not alert_data.get('tp') or not alert_data.get('sl'))):
                trade_result = {
                    'success': False,
                    'error': 'Take Profit and Stop Loss values are required for automatic trading',
                    'trade_executed': False
                }
            else:
                should_execute_trade = True
        
        # Execute trade if all checks pass
        if should_execute_trade:
            logger.info("All safety checks passed, executing automatic Binance futures trade...")
            try:
                trade_result = execute_tradingview_trade(alert_data)
                logger.info(f"Binance trade execution result: {trade_result}")
                
                # Increment daily trade counter if trade was successful
                if trade_result.get('trade_executed'):
                    auto_trading_config['daily_trade_count'] += 1
                    logger.info(f"Daily trade count: {auto_trading_config['daily_trade_count']}/{auto_trading_config['max_daily_trades']}")
                    
            except Exception as trade_error:
                logger.error(f"Error executing automatic Binance trade: {str(trade_error)}")
                trade_result = {
                    'success': False,
                    'error': f'Trade execution failed: {str(trade_error)}',
                    'trade_executed': False
                }
        
        # Store trade result in alert data
        alert_data['trade_result'] = trade_result
        
        # Prepare response
        response = {
            'success': True,
            'message': 'Binance webhook alert received successfully',
            'alert_id': len(received_alerts),
            'timestamp': alert_data['timestamp'],
            'is_valid': alert_data.get('is_valid', False),
            'trade_executed': trade_result.get('trade_executed', False) if trade_result else False
        }
        
        # Include validation errors in response if any
        if alert_data.get('validation_errors'):
            response['validation_errors'] = alert_data['validation_errors']
            response['message'] = 'Binance webhook alert received with validation warnings'
        
        # Include trade execution result
        if trade_result:
            response['trade_result'] = trade_result
        
        # Update message based on result
        if trade_result and trade_result.get('trade_executed'):
            response['message'] = 'Alert received and Binance futures trade executed successfully'
        elif not alert_data.get('is_valid', False):
            response['message'] = 'Alert received but failed validation - no Binance trade executed'
        elif not auto_trading_config['enabled']:
            response['message'] = 'Alert received but automatic trading is disabled'
        else:
            response['message'] = 'Alert received but Binance trade execution failed'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing TradingView Binance webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Binance webhook error: {str(e)}'
        }), 500

@tradingview_bp.route('/tradingview/symbols', methods=['POST'])
def receive_selected_symbols():
    """
    Receive selected cryptocurrency symbols for monitoring
    This endpoint provides instructions for manual TradingView setup
    """
    try:
        data = request.get_json()
        
        if not data or 'symbols' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing symbols in request body'
            }), 400
        
        symbols = data['symbols']
        
        # Generate TradingView setup instructions
        instructions = []
        for symbol in symbols:
            symbol_upper = symbol.upper()
            instructions.append({
                'symbol': symbol_upper,
                'tradingview_symbol': f"{symbol_upper}USD",
                'setup_steps': [
                    f"1. Open TradingView and search for '{symbol_upper}USD'",
                    "2. Add the symbol to your watchlist or open a chart",
                    "3. Create an alert by clicking the 'Alert' button",
                    "4. Set your desired conditions (price, indicators, etc.)",
                    "5. In 'Notifications' tab, enable 'Webhook URL'",
                    "6. Choose webhook URL based on your needs:",
                    f"   - Both Binance + MT4: {request.host_url}api/tradingview/webhook",
                    f"   - Binance only: {request.host_url}api/tradingview/binance/webhook", 
                    f"   - MT4 only: {request.host_url}api/tradingview/mt4/webhook",
                    "7. In the message field, use JSON format (choose one):",
                    "   Old format:",
                    f'   {{"symbol": "{symbol_upper}USD", "action": "buy", "price": {{{{close}}}}, "tp": {{{{close}}}}*1.02, "sl": {{{{close}}}}*0.98, "quantity": 0.001, "message": "Alert triggered"}}',
                    "   New format:", 
                    f'   {{"alert_type": "BUY", "name_of_strategy": "AllBestSignal-V1", "signal": "LONG", "entry_price": {{{{close}}}}, "tp": {{{{close}}}}*1.02, "sl": {{{{close}}}}*0.98, "quantity": 1.0, "symbol": "{symbol_upper}USD"}}',
                    "8. Save the alert"
                ]
            })
        
        return jsonify({
            'success': True,
            'message': f'Setup instructions generated for {len(symbols)} symbols',
            'webhook_urls': {
                'all_platforms': f"{request.host_url}api/tradingview/webhook",
                'binance_only': f"{request.host_url}api/tradingview/binance/webhook",
                'mt4_only': f"{request.host_url}api/tradingview/mt4/webhook"
            },
            'symbols': symbols,
            'instructions': instructions,
            'parameter_description': {
                'Old Format Fields': {
                    'symbol': 'Trading pair symbol (e.g., BTCUSD)',
                    'action': 'Trading action: "buy" or "sell"',
                    'price': 'Current price when alert triggers (use {{close}} for current price)',
                    'tp': 'Take profit price - exact price will be used in orders (optional)',
                    'sl': 'Stop loss price - exact price will be used in orders (optional)',
                    'quantity': 'Trade quantity/amount (optional)',
                    'message': 'Custom alert message (optional)'
                },
                'New Format Fields': {
                    'alert_type': 'Alert type: "BUY", "SELL", "LONG", or "SHORT"',
                    'name_of_strategy': 'Strategy name identifier',
                    'signal': 'Signal direction: "LONG" or "SHORT"',
                    'entry_price': 'Entry price when alert triggers (use {{close}} for current price)',
                    'tp': 'Take profit price - exact price will be used in orders (optional)',
                    'sl': 'Stop loss price - exact price will be used in orders (optional)',
                    'quantity': 'Trade quantity/amount (for MT4: ignored, uses EA lot size)',
                    'symbol': 'Trading pair symbol (e.g., EURUSD)'
                }
            },
            'example_old_format_buy': {
                'symbol': 'BTCUSD',
                'action': 'buy',
                'price': '{{close}}',
                'tp': '{{close}}*1.02',
                'sl': '{{close}}*0.98',
                'quantity': 0.001,
                'message': 'Buy signal - old format'
            },
            'example_new_format_buy': {
                'alert_type': 'BUY',
                'name_of_strategy': 'AllBestSignal-V1',
                'signal': 'LONG',
                'entry_price': '{{close}}',
                'tp': '{{close}}*1.02',
                'sl': '{{close}}*0.98',
                'quantity': 1.0,
                'symbol': 'EURUSD'
            },
            'example_new_format_sell': {
                'alert_type': 'SELL',
                'name_of_strategy': 'AllBestSignal-V1',
                'signal': 'SHORT',
                'entry_price': '{{close}}',
                'tp': '{{close}}*0.98',
                'sl': '{{close}}*1.02',
                'quantity': 1.0,
                'symbol': 'EURUSD'
            },
            'webhook_info': {
                'all_platforms': 'Executes trades on both Binance Futures and MT4 simultaneously',
                'binance_only': 'Executes trades only on Binance Futures (crypto trading)',
                'mt4_only': 'Sends signals only to MT4 (forex trading, quantity ignored - uses EA lot size)'
            },
            'format_support': 'All webhooks support both old format (action/price) and new format (alert_type/entry_price)',
            'mt4_quantity_note': 'For MT4-only webhook, the quantity parameter is ignored and the EA uses its configured default lot size',
            'note': 'TradingView does not provide API for programmatic chart setup. Please follow the manual setup instructions. The exact TP/SL prices from TradingView will be used in orders without modification.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

