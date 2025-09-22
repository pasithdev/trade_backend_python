from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from src.routes.binance_trading import binance_bp
from src.routes.tradingview import received_alerts

integration_bp = Blueprint('integration', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@integration_bp.route('/integration/tradingview-to-binance', methods=['POST'])
def tradingview_to_binance():
    """
    Enhanced webhook endpoint that receives TradingView alerts and automatically executes Binance trades
    This combines the TradingView webhook functionality with Binance trading execution
    """
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
                import json
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text message
                data = {'message': raw_data}
        
        # Add timestamp and source info
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'tradingview_integration',
            'raw_data': data,
            'processed': False
        }
        
        # Try to extract standard fields
        if isinstance(data, dict):
            symbol = data.get('symbol', 'UNKNOWN')
            action = data.get('action', 'unknown').lower()
            price = data.get('price')
            message = data.get('message', str(data))
        else:
            symbol = 'UNKNOWN'
            action = 'unknown'
            price = None
            message = str(data)
        
        alert_data.update({
            'symbol': symbol,
            'action': action,
            'price': price,
            'message': message
        })
        
        # Store the alert in the TradingView alerts list
        received_alerts.append(alert_data)
        
        # Keep only the last 100 alerts
        if len(received_alerts) > 100:
            received_alerts[:] = received_alerts[-100:]
        
        # Log the received alert
        logger.info(f"Received TradingView integration alert: {alert_data}")
        
        # Process the alert for trading if it's valid
        trade_result = None
        if symbol != 'UNKNOWN' and action in ['buy', 'sell']:
            try:
                # Prepare trade data for Binance
                trade_data = {
                    'symbol': symbol.replace('USD', 'USDT'),  # Convert BTCUSD to BTCUSDT
                    'action': action,
                    'order_value': 20.0,  # Default order value in USDT
                    'tp_percentage': 2.0,  # 2% take profit
                    'sl_percentage': 1.0   # 1% stop loss
                }
                
                # Import the execute_trade function
                from src.routes.binance_trading import execute_trade, binance_client
                
                if binance_client:
                    # Create a test request context to call execute_trade
                    with integration_bp.test_request_context('/binance/trade', method='POST', json=trade_data):
                        trade_response = execute_trade()
                        
                    if hasattr(trade_response, 'get_json'):
                        trade_result = trade_response.get_json()
                    else:
                        trade_result = trade_response
                    
                    # Mark alert as processed
                    alert_data['processed'] = True
                    alert_data['trade_result'] = trade_result
                    
                    logger.info(f"Trade executed for alert: {trade_result}")
                else:
                    trade_result = {
                        'success': False,
                        'error': 'Binance client not configured'
                    }
                    
            except Exception as trade_error:
                trade_result = {
                    'success': False,
                    'error': f'Trade execution failed: {str(trade_error)}'
                }
                logger.error(f"Trade execution error: {str(trade_error)}")
        
        # Prepare response
        response_data = {
            'success': True,
            'message': 'Alert received and processed',
            'alert': {
                'symbol': symbol,
                'action': action,
                'price': price,
                'message': message,
                'processed': alert_data['processed']
            },
            'timestamp': alert_data['timestamp']
        }
        
        if trade_result:
            response_data['trade_execution'] = trade_result
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing TradingView to Binance integration: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Integration error: {str(e)}'
        }), 500

@integration_bp.route('/integration/status', methods=['GET'])
def get_integration_status():
    """Get the status of all integrations"""
    try:
        from src.routes.binance_trading import binance_client, trading_config
        from src.routes.tradingview import received_alerts
        
        # Check Binance connection status
        binance_status = {
            'connected': binance_client is not None,
            'testnet': trading_config.get('testnet', True),
            'config': {
                'tp_percentage': trading_config.get('default_tp_percentage', 2.0),
                'sl_percentage': trading_config.get('default_sl_percentage', 1.0),
                'min_order_value': trading_config.get('min_order_value', 10.0),
                'max_order_value': trading_config.get('max_order_value', 1000.0)
            }
        }
        
        # Check TradingView alerts status
        tradingview_status = {
            'total_alerts': len(received_alerts),
            'processed_alerts': len([alert for alert in received_alerts if alert.get('processed', False)]),
            'recent_alerts': received_alerts[-5:] if received_alerts else []
        }
        
        return jsonify({
            'success': True,
            'integration_status': {
                'binance': binance_status,
                'tradingview': tradingview_status,
                'webhook_url': f"{request.host_url}api/integration/tradingview-to-binance"
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting integration status: {str(e)}'
        }), 500

@integration_bp.route('/integration/test', methods=['POST'])
def test_integration():
    """Test the complete integration flow"""
    try:
        data = request.get_json() or {}
        
        # Create a test alert
        test_alert = {
            'symbol': data.get('symbol', 'BTCUSDT'),
            'action': data.get('action', 'buy'),
            'price': data.get('price', 50000.0),
            'message': 'Test integration alert'
        }
        
        # Send the test alert to the integration endpoint
        with integration_bp.test_request_context('/integration/tradingview-to-binance', 
                                                method='POST', 
                                                json=test_alert,
                                                headers={'Content-Type': 'application/json'}):
            response = tradingview_to_binance()
            
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Integration test error: {str(e)}'
        }), 500

