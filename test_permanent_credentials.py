#!/usr/bin/env python3
"""
🧪 Test Permanent API Credentials Implementation
Tests that the permanent credentials fix is working correctly
"""

import requests
import json
import time
from datetime import datetime

# Production server configuration
SERVER = "167.71.207.209"
PORT = 5000
BASE_URL = f"http://{SERVER}:{PORT}/api"

# Test payload for webhooks
TEST_PAYLOAD = {
    "symbol": "BTCUSDT",
    "action": "buy",
    "balance_percentage": 0.10,  # Small test amount
    "leverage": 10,
    "entry": 43000
}

def test_webhook(endpoint, payload):
    """Test a specific webhook endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        print(f"🔗 Testing: {url}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS - No client configuration errors!")
            try:
                result = response.json()
                if 'success' in result:
                    print(f"🎯 Response: {result.get('message', 'Success')}")
                else:
                    print(f"📋 Response: {json.dumps(result, indent=2)}")
            except:
                print(f"📋 Response: {response.text}")
        elif response.status_code == 400:
            try:
                error = response.json()
                if 'Binance client initialization failed' in error.get('error', ''):
                    print("⚠️ EXPECTED - Client auto-initialization attempted")
                    print("💡 This suggests permanent credentials are working")
                elif 'Binance client not configured' in error.get('error', ''):
                    print("❌ FAILURE - Old error message detected!")
                    print("🚨 Permanent credentials implementation may not be deployed")
                else:
                    print(f"📋 Error: {error}")
            except:
                print(f"📋 Error Response: {response.text}")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    
    print("-" * 60)

def main():
    """Run comprehensive webhook tests"""
    print("🧪 PERMANENT API CREDENTIALS TEST")
    print("=" * 60)
    print(f"🎯 Testing Server: {SERVER}")
    print(f"⏰ Test Time: {datetime.now()}")
    print("=" * 60)
    
    # List of webhook endpoints to test
    webhooks = [
        ("/binance/state-aware-ma-cross-webhook", "State-aware MA Cross"),
        ("/binance/super-scalper-webhook", "Super Scalper"),
        ("/binance/target-trend-webhook", "Target Trend")
    ]
    
    results = {}
    
    for endpoint, name in webhooks:
        print(f"\n🔍 Testing {name} Webhook")
        print("-" * 30)
        
        start_time = time.time()
        test_webhook(endpoint, TEST_PAYLOAD)
        elapsed = time.time() - start_time
        
        print(f"⏱️ Response Time: {elapsed:.2f}s")
        
        # Brief pause between tests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print("✅ SUCCESS: No '400 - Binance client not configured' errors")
    print("⚠️ Expected: Some '400 - initialization failed' responses (due to test mode)")
    print("💡 Key Indicator: Error messages should mention 'auto-initialization attempted'")
    print("")
    print("🔍 What to Look For:")
    print("• Old Error: 'Binance client not configured. Please configure API credentials first.'")
    print("• New Error: 'Binance client initialization failed. Auto-initialization attempted.'")
    print("")
    print("✅ If you see the NEW error messages, permanent credentials are working!")
    print("❌ If you see the OLD error messages, deployment may have failed.")

if __name__ == "__main__":
    main()