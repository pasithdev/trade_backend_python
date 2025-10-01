#!/usr/bin/env python3
"""
Test script for the new Smart Webhook with configurable quantity percentage and leverage
"""

import requests
import json

def test_smart_webhook():
    """Test the smart webhook with different scenarios"""
    
    # Webhook URL
    webhook_url = "http://localhost:80/api/binance/smart-webhook"
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Buy with defaults (20% quantity, 10x leverage)",
            "data": {
                "action": "buy",
                "symbol": "ADAUSDT",  # Lower minimum quantity than BTC
                "entry": "0.50"
            }
        },
        {
            "name": "Sell with custom settings",
            "data": {
                "action": "sell", 
                "symbol": "DOGEUSDT",
                "quantity_percent": 0.15,  # 15%
                "leverage": 8,
                "entry": "0.08",
                "sl_percent": 1.5,
                "tp_percent": 3.0
            }
        },
        {
            "name": "Long position (alias for buy)",
            "data": {
                "action": "long",
                "symbol": "ETHUSDT",
                "quantity_percent": 0.10,  # 10%
                "leverage": 5,
                "entry": "3500.00"
            }
        },
        {
            "name": "Close all positions",
            "data": {
                "action": "close",
                "symbol": "ADAUSDT"
            }
        }
    ]
    
    print("Testing Smart Webhook with Configurable Settings")
    print(f"URL: {webhook_url}")
    print("=" * 60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"Data: {json.dumps(scenario['data'], indent=2)}")
        print("-" * 40)
        
        try:
            # Send POST request to webhook
            response = requests.post(
                webhook_url,
                json=scenario['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Test PASSED")
                    trade = result.get('trade', {})
                    print(f"   Action: {trade.get('action', 'N/A')}")
                    print(f"   Symbol: {trade.get('symbol', 'N/A')}")
                    print(f"   Quantity: {trade.get('quantity', 'N/A')}")
                    print(f"   Quantity %: {trade.get('quantity_percent_display', 'N/A')}")
                    print(f"   Leverage: {trade.get('leverage', 'N/A')}x")
                    print(f"   Order ID: {trade.get('main_order_id', 'N/A')}")
                    
                    # Show calculation details
                    calc = result.get('calculation_details', {})
                    if calc:
                        print(f"   Balance Used: {calc.get('available_balance', 'N/A')} USDT")
                        print(f"   Position Value: {calc.get('position_value_usdt', 'N/A')} USDT")
                        print(f"   Current Price: {calc.get('current_price', 'N/A')} USDT")
                else:
                    print(f"❌ Test FAILED: {result.get('error')}")
                    if result.get('suggestions'):
                        print("   Suggestions:")
                        for suggestion in result.get('suggestions', []):
                            print(f"   - {suggestion}")
            else:
                try:
                    error_info = response.json()
                    print(f"❌ HTTP Error {response.status_code}: {error_info.get('error', 'Unknown error')}")
                except:
                    print(f"❌ HTTP Error {response.status_code}: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
            print("Make sure the Flask server is running on localhost:80")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
        
        print()

def test_get_smart_webhook_info():
    """Get smart webhook information"""
    
    info_url = "http://localhost:80/api/binance/test-smart_webhook"
    
    try:
        response = requests.post(info_url, timeout=10)
        if response.status_code == 200:
            info = response.json()
            print("📋 Smart Webhook Information:")
            print(f"   Main URL: {info.get('webhook_url')}")
            print(f"   Alt URL: {info.get('alternative_url')}")
            
            defaults = info.get('defaults', {})
            print(f"\n   Defaults:")
            print(f"   - Quantity: {defaults.get('quantity_percent', 0)*100}%")
            print(f"   - Leverage: {defaults.get('leverage')}x")
            print(f"   - Stop Loss: {defaults.get('sl_percent')}%")
            print(f"   - Take Profit: {defaults.get('tp_percent')}%")
            
            print(f"\n   Features:")
            for feature in info.get('features', []):
                print(f"   • {feature}")
        
    except Exception as e:
        print(f"Could not get webhook info: {e}")

def test_quantity_calculation():
    """Test quantity calculation for different symbols"""
    
    symbols_to_test = ["ADAUSDT", "DOGEUSDT", "ETHUSDT", "BTCUSDT"]
    percentages = [0.05, 0.10, 0.20, 0.30]  # 5%, 10%, 20%, 30%
    
    print("\n" + "=" * 60)
    print("QUANTITY CALCULATION TEST")
    print("=" * 60)
    
    for symbol in symbols_to_test:
        print(f"\n{symbol}:")
        for pct in percentages:
            test_data = {
                "action": "buy",
                "symbol": symbol,
                "quantity_percent": pct
            }
            
            try:
                response = requests.post(
                    "http://localhost:80/api/binance/smart-webhook",
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    trade = result.get('trade', {})
                    calc = result.get('calculation_details', {})
                    print(f"  {pct*100:2.0f}%: {trade.get('quantity', 'N/A')} (${calc.get('position_value_usdt', 'N/A'):.2f})")
                else:
                    error = response.json().get('error', 'Unknown error')
                    print(f"  {pct*100:2.0f}%: ❌ {error}")
                    
            except Exception as e:
                print(f"  {pct*100:2.0f}%: ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Smart Webhook Testing Suite")
    print("Testing webhook with configurable quantity % and leverage")
    
    # Test webhook info first
    test_get_smart_webhook_info()
    
    # Test main webhook functionality
    test_smart_webhook()
    
    # Test quantity calculations
    test_quantity_calculation()
    
    print("\n✅ Testing complete!")