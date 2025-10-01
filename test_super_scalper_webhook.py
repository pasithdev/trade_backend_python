"""
Test script for Professional Crypto Super Scalper webhook
Tests different scalping scenarios and signal strengths
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Change to your server URL
TEST_ENDPOINT = f"{BASE_URL}/binance/test-super-scalper-webhook"
WEBHOOK_ENDPOINT = f"{BASE_URL}/binance/super-scalper-webhook"

def test_super_scalper_info():
    """Test the Super Scalper webhook info endpoint"""
    print("🎯 Testing Super Scalper webhook info...")
    
    try:
        response = requests.post(TEST_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Super Scalper webhook info retrieved successfully")
            print(f"📊 Default settings: {data.get('scalping_defaults', {})}")
            print(f"🔧 Features: {len(data.get('features', []))} professional features")
            return True
        else:
            print(f"❌ Failed to get Super Scalper info: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing Super Scalper info: {e}")
        return False

def test_super_scalper_webhook(test_name, webhook_data):
    """Test the Super Scalper webhook with specific data"""
    print(f"\n🧪 Testing: {test_name}")
    print(f"📤 Sending: {json.dumps(webhook_data, indent=2)}")
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Super Scalper webhook executed successfully!")
            
            # Print key trade information
            if 'trade' in data:
                trade = data['trade']
                print(f"🎯 Trade: {trade['action']} {trade['quantity']} {trade['symbol']}")
                print(f"💰 Position Size: {trade['quantity_percent_display']}")
                print(f"🔢 Leverage: {trade['leverage']}x")
                
                if 'stop_loss' in trade and trade['stop_loss']['enabled']:
                    print(f"🛑 Stop Loss: {trade['stop_loss']['price']} ({trade['stop_loss']['percent']}%)")
                
                if 'take_profit' in trade and trade['take_profit']['enabled']:
                    print(f"🎯 Take Profit: {trade['take_profit']['price']} ({trade['take_profit']['percent']}%)")
            
            # Print signal analysis
            if 'signal_analysis' in data:
                analysis = data['signal_analysis']
                print(f"📊 Signal Analysis:")
                print(f"  - Strength: {analysis.get('signal_strength', 'N/A')}")
                print(f"  - Risk Level: {analysis.get('risk_level', 'N/A')}")
                print(f"  - Market Condition: {analysis.get('market_condition', 'N/A')}")
                print(f"  - Position Adjusted: {analysis.get('adjusted_quantity', 'N/A')}")
            
            return True
            
        else:
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"❌ Super Scalper webhook failed: {data.get('error', 'Unknown error')}")
            
            if 'suggestions' in data:
                print("💡 Suggestions:")
                for suggestion in data['suggestions']:
                    print(f"  - {suggestion}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error testing Super Scalper webhook: {e}")
        return False

def main():
    """Run comprehensive Super Scalper webhook tests"""
    print("🚀 Professional Crypto Super Scalper Webhook Test Suite")
    print("=" * 60)
    
    # Test 1: Get webhook information
    if not test_super_scalper_info():
        print("❌ Failed to get Super Scalper webhook info. Check if server is running.")
        return
    
    print("\n" + "=" * 60)
    print("🧪 Running Super Scalper Trading Tests")
    
    # Test scenarios for Professional Crypto Super Scalper
    test_scenarios = [
        {
            "name": "Strong Long Signal - Trending Market",
            "data": {
                "action": "long",
                "symbol": "ETHUSDT",
                "quantity_percent": 0.15,  # 15% base
                "leverage": 20,
                "entry": "3456.78",
                "signal_strength": "strong",    # Will increase position to 22.5%
                "risk_level": "medium",
                "market_condition": "trending",
                "sl_percent": 0.8,
                "tp_percent": 1.2
            }
        },
        {
            "name": "Weak Short Signal - High Risk",
            "data": {
                "action": "short",
                "symbol": "BTCUSDT",
                "quantity_percent": 0.12,  # 12% base
                "leverage": 15,
                "entry": "67890.12",
                "signal_strength": "weak",     # Will reduce position
                "risk_level": "high",         # Will further reduce and cap leverage
                "market_condition": "normal",
                "sl_percent": 0.8,
                "tp_percent": 1.2
            }
        },
        {
            "name": "Normal Signal - Volatile Market",
            "data": {
                "action": "buy",
                "symbol": "ADAUSDT",
                "quantity_percent": 0.10,  # 10% base
                "leverage": 12,
                "entry": "0.8234",
                "signal_strength": "normal",
                "risk_level": "medium",
                "market_condition": "volatile",  # Will adjust stops/targets
                "sl_percent": 0.8,
                "tp_percent": 1.2
            }
        },
        {
            "name": "Strong Signal - Ranging Market",
            "data": {
                "action": "sell",
                "symbol": "DOGEUSDT",
                "quantity_percent": 0.08,  # 8% base
                "leverage": 18,
                "entry": "0.08234",
                "signal_strength": "strong",    # Will increase position
                "risk_level": "low",           # Will further increase
                "market_condition": "ranging", # Will adjust targets
                "sl_percent": 0.8,
                "tp_percent": 1.2
            }
        },
        {
            "name": "Emergency Exit - All Positions",
            "data": {
                "action": "emergency_exit",
                "symbol": "BTCUSDT",
                "signal_strength": "strong",
                "risk_level": "high",
                "market_condition": "volatile"
            }
        },
        {
            "name": "Simplified Long Signal (TradingView format)",
            "data": {
                "action": "long",
                "symbol": "ETHUSDT",
                "entry": "3456.78"
                # Will use all defaults: 15%, 20x leverage, 0.8% SL, 1.2% TP
            }
        },
        {
            "name": "Close All Positions",
            "data": {
                "action": "close",
                "symbol": "ADAUSDT"
            }
        }
    ]
    
    # Run all test scenarios
    passed_tests = 0
    total_tests = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}/{total_tests}: {scenario['name']}")
        print("-" * 40)
        
        if test_super_scalper_webhook(scenario['name'], scenario['data']):
            passed_tests += 1
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
        
        # Small delay between tests
        if i < total_tests:
            time.sleep(2)
    
    # Test summary
    print("\n" + "=" * 60)
    print("📊 SUPER SCALPER TEST SUMMARY")
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All Super Scalper tests passed! Webhook is ready for professional scalping.")
    else:
        print("⚠️  Some tests failed. Please check the errors above and fix any issues.")
    
    print("\n🔗 Webhook URLs:")
    print(f"  - Main Endpoint: {WEBHOOK_ENDPOINT}")
    print(f"  - Test Endpoint: {TEST_ENDPOINT}")
    
    print("\n📚 Next Steps:")
    print("1. Configure your TradingView alerts with the webhook URL")
    print("2. Use the Professional Crypto Super Scalper Pine Script")
    print("3. Start with testnet before live trading")
    print("4. Monitor logs for detailed execution information")

if __name__ == "__main__":
    main()