#!/usr/bin/env python3
"""
Test script to verify Binance API logging functionality
"""

import requests
import json
import time

def test_binance_api_logging():
    """Test that Binance API logging is working properly"""
    
    # Test the connection test endpoint which makes several API calls
    test_url = "http://localhost:5000/api/binance/test"
    
    print("🧪 Testing Binance API Logging")
    print(f"URL: {test_url}")
    print("-" * 60)
    
    try:
        # Send POST request to test endpoint
        response = requests.post(test_url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test Response: {json.dumps(result, indent=2)}")
            print("\n" + "="*60)
            print("📋 Check your application logs for the following entries:")
            print("   - BINANCE API CALL - get_server_time")
            print("   - BINANCE API CALL - futures_account") 
            print("   - BINANCE API CALL - futures_symbol_ticker")
            print("   - BINANCE API CALL - futures_exchange_info")
            print("="*60)
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_webhook_logging():
    """Test webhook API logging with sample data"""
    
    webhook_url = "http://localhost:80/api/binance/state-aware-ma-cross-webhook"
    
    # Test data for buy signal
    test_data = {
        "action": "buy",
        "symbol": "BTCUSDT", 
        "balance_percentage": "0.10",  # Use small amount for testing
        "leverage": "5",  # Lower leverage for testing
        "entry": "50000.00"
    }
    
    print("\n🚀 Testing Webhook API Logging")
    print(f"URL: {webhook_url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook Response: {json.dumps(result, indent=2)}")
            print("\n" + "="*60)
            print("📋 Check your application logs for trading API calls:")
            print("   - BINANCE API CALL - futures_account (for quantity calculation)")
            print("   - BINANCE API CALL - futures_symbol_ticker (for current price)")
            print("   - BINANCE API CALL - futures_exchange_info (for symbol info)")
            print("   - BINANCE API CALL - futures_position_information (for position check)")
            print("   - BINANCE API CALL - futures_change_leverage (set leverage)")
            print("   - BINANCE API CALL - futures_change_margin_type (set margin)")
            print("   - BINANCE API CALL - futures_create_order (main buy order)")
            print("="*60)
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_binance_api_logging()
    time.sleep(2)  # Wait a bit between tests
    test_webhook_logging()