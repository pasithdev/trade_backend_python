#!/usr/bin/env python3
"""
Test script for the updated State-aware MA Cross webhook close functionality
"""

import requests
import json

# Test the close webhook functionality
def test_close_webhook():
    """Test the close webhook with sample data"""
    
    # Webhook URL (adjust port if needed)
    webhook_url = "http://localhost:5000/api/binance/state-aware-ma-cross-webhook"
    
    # Test data for close signal
    test_data = {
        "action": "close",
        "symbol": "BTCUSDT", 
        "leverage": "10",
        "entry": "50000.00"
    }
    
    print("Testing State-aware MA Cross Close Webhook")
    print(f"URL: {webhook_url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        # Send POST request to webhook
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✅ Close webhook test PASSED")
                if result.get('closed_positions'):
                    print(f"   - Closed {len(result['closed_positions'])} position(s)")
                    for pos in result['closed_positions']:
                        print(f"   - {pos['position_type'].upper()}: {pos['side']} {pos['quantity']} (Order: {pos['order_id']})")
                else:
                    print("   - No positions were open to close")
            else:
                print(f"❌ Close webhook test FAILED: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_get_info():
    """Get webhook information"""
    
    info_url = "http://localhost:5000/api/binance/test-state-aware-close"
    
    try:
        response = requests.post(info_url, timeout=10)
        if response.status_code == 200:
            info = response.json()
            print("\n📋 Webhook Information:")
            print(f"   - Test URL: {info.get('alternative_url')}")
            print("   - Features:")
            for feature in info.get('features', []):
                print(f"     • {feature}")
        
    except Exception as e:
        print(f"Could not get webhook info: {e}")

if __name__ == "__main__":
    test_get_info()
    print()
    test_close_webhook()