#!/usr/bin/env python3
"""
Test script for the Advanced Trading Webhook
Tests buy, sell, and close actions with automatic position sizing
"""

import requests
import json
import time

# Configuration
SERVER = "http://localhost:80/api"
WEBHOOK_ENDPOINT = f"{SERVER}/binance/advanced-trading-webhook"

def test_buy_signal():
    """Test buy signal with automatic position sizing"""
    payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.25,  # 25% of balance
        "leverage": 10,
        "entry": 50000.0
    }
    
    print("=" * 60)
    print("🟢 Testing BUY Signal")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        if response.status_code == 200:
            print("✅ BUY Signal - SUCCESS\n")
            return True
        else:
            print("❌ BUY Signal - FAILED\n")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False

def test_sell_signal():
    """Test sell signal with automatic position sizing"""
    payload = {
        "symbol": "ETHUSDT",
        "action": "sell",
        "balance_percentage": 0.20,  # 20% of balance
        "leverage": 15,
        "entry": 3000.0
    }
    
    print("=" * 60)
    print("🔴 Testing SELL Signal")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        if response.status_code == 200:
            print("✅ SELL Signal - SUCCESS\n")
            return True
        else:
            print("❌ SELL Signal - FAILED\n")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False

def test_close_signal():
    """Test close signal - closes all positions for symbol"""
    payload = {
        "symbol": "BTCUSDT",
        "action": "close",
        "balance_percentage": 0.25,  # Not used for close
        "leverage": 10,
        "entry": 50000.0
    }
    
    print("=" * 60)
    print("⚫ Testing CLOSE Signal")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        if response.status_code == 200:
            print("✅ CLOSE Signal - SUCCESS\n")
            return True
        else:
            print("❌ CLOSE Signal - FAILED\n")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False

def test_invalid_action():
    """Test invalid action to verify error handling"""
    payload = {
        "symbol": "BTCUSDT",
        "action": "invalid_action",
        "balance_percentage": 0.25,
        "leverage": 10,
        "entry": 50000.0
    }
    
    print("=" * 60)
    print("⚠️ Testing INVALID Action (Error Handling)")
    print("=" * 60)
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        
        if response.status_code == 400:
            print("✅ Error Handling - SUCCESS (Correctly rejected invalid action)\n")
            return True
        else:
            print("❌ Error Handling - FAILED (Should have rejected invalid action)\n")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False

def main():
    """Run all webhook tests"""
    print("\n" + "=" * 60)
    print("🧪 ADVANCED TRADING WEBHOOK TEST SUITE")
    print("=" * 60)
    print(f"🎯 Testing Server: {SERVER}")
    print(f"📍 Endpoint: {WEBHOOK_ENDPOINT}")
    print(f"⏰ Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    results = {
        'buy': False,
        'sell': False,
        'close': False,
        'error_handling': False
    }
    
    # Test buy signal
    results['buy'] = test_buy_signal()
    time.sleep(2)
    
    # Test sell signal
    results['sell'] = test_sell_signal()
    time.sleep(2)
    
    # Test close signal
    results['close'] = test_close_signal()
    time.sleep(2)
    
    # Test error handling
    results['error_handling'] = test_invalid_action()
    
    # Print summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")
    
    print("-" * 60)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print("=" * 60 + "\n")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - Please review the results above")

if __name__ == "__main__":
    main()
