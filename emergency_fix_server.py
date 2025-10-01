#!/usr/bin/env python3
"""
Emergency Server Fix Script - Run this to fix the intermittent 400 errors
This script will connect to your server and apply the critical fixes
"""

import requests
import time
import json

SERVER_IP = "167.71.207.209"
BASE_URL = f"http://{SERVER_IP}"

API_KEY = "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ"
API_SECRET = "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF"

def fix_api_configuration():
    """Fix the API configuration issue"""
    print("🔧 FIXING API CONFIGURATION...")
    
    config_payload = {
        "api_key": API_KEY,
        "api_secret": API_SECRET,
        "testnet": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/binance/config",
            json=config_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ API configuration successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ API configuration failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API configuration error: {e}")

def verify_api_status():
    """Verify API configuration is working"""
    print("\n🔍 VERIFYING API STATUS...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/binance/status", timeout=10)
        
        if response.status_code == 200:
            print("✅ API status check successful!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ API status check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API status check error: {e}")
        return False

def test_webhooks_with_optimized_sizes():
    """Test webhooks with optimized position sizes"""
    print("\n🧪 TESTING WEBHOOKS WITH OPTIMIZED SIZES...")
    
    # Test configurations with larger position sizes to meet minimum requirements
    test_configs = [
        {
            "endpoint": "/api/binance/state-aware-ma-cross-webhook",
            "payload": {
                "symbol": "ETHUSDT",
                "action": "buy",
                "balance_percentage": 0.50,  # 50% for $20+ position
                "leverage": 10,
                "entry": 2456.78
            }
        },
        {
            "endpoint": "/api/binance/state-aware-ma-cross-webhook", 
            "payload": {
                "symbol": "BTCUSDT",
                "action": "buy",
                "balance_percentage": 0.80,  # 80% for high-value BTC
                "leverage": 5,
                "entry": 43000.0
            }
        },
        {
            "endpoint": "/api/binance/state-aware-ma-cross-webhook",
            "payload": {
                "symbol": "DOGEUSDT", 
                "action": "buy",
                "balance_percentage": 0.30,  # 30% for DOGE's $5 minimum
                "leverage": 10,
                "entry": 0.12
            }
        }
    ]
    
    success_count = 0
    
    for config in test_configs:
        endpoint = config["endpoint"]
        payload = config["payload"]
        symbol = payload["symbol"]
        
        print(f"\n--- Testing {symbol} ---")
        
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"✅ {symbol}: SUCCESS!")
                print(f"Response: {response.json()}")
                success_count += 1
            else:
                print(f"❌ {symbol}: FAILED ({response.status_code})")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ {symbol}: CONNECTION ERROR - {e}")
    
    print(f"\n📊 Success Rate: {success_count}/{len(test_configs)} ({success_count/len(test_configs)*100:.1f}%)")
    return success_count == len(test_configs)

def stress_test_stability():
    """Test webhook stability over multiple calls"""
    print("\n⚡ STRESS TESTING STABILITY...")
    
    test_payload = {
        "symbol": "ETHUSDT",
        "action": "buy", 
        "balance_percentage": 0.50,
        "leverage": 10,
        "entry": 2456.78
    }
    
    success_count = 0
    api_config_failures = 0
    
    for i in range(20):
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/state-aware-ma-cross-webhook",
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                success_count += 1
                if i % 5 == 0:
                    print(f"✅ Test {i+1}: SUCCESS")
            else:
                error_text = response.text.lower()
                if "not configured" in error_text:
                    api_config_failures += 1
                    print(f"🔧 Test {i+1}: API CONFIG LOST - Reconfiguring...")
                    # Immediately reconfigure API
                    fix_api_configuration()
                    time.sleep(1)
                else:
                    print(f"❌ Test {i+1}: OTHER ERROR ({response.status_code})")
                    
        except Exception as e:
            print(f"❌ Test {i+1}: CONNECTION ERROR")
        
        time.sleep(0.5)
    
    print(f"\n📊 Stability Results:")
    print(f"   Success Rate: {success_count}/20 ({success_count/20*100:.1f}%)")
    print(f"   API Config Losses: {api_config_failures}")
    
    return success_count >= 15  # 75% success threshold

def main():
    """Run emergency server fix"""
    print("🚨 EMERGENCY SERVER FIX STARTING...")
    print(f"Target Server: {SERVER_IP}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Fix API configuration  
    fix_api_configuration()
    time.sleep(2)
    
    # Step 2: Verify API status
    if not verify_api_status():
        print("❌ CRITICAL: API configuration failed!")
        return False
    
    time.sleep(2)
    
    # Step 3: Test webhooks with optimized sizes
    if not test_webhooks_with_optimized_sizes():
        print("⚠️ WARNING: Some webhook tests failed")
    
    time.sleep(2)
    
    # Step 4: Stability stress test
    if stress_test_stability():
        print("\n🎉 SUCCESS: Server appears stable!")
    else:
        print("\n⚠️ WARNING: Server still showing instability")
    
    print("\n📋 NEXT STEPS:")
    print("1. Monitor server logs: SSH and run 'tail -f trading_system.log'")
    print("2. If API config keeps getting lost, restart the Python application")
    print("3. Consider implementing persistent API credential storage")
    print("4. Monitor position sizes to ensure they meet Binance minimums")
    
    return True

if __name__ == "__main__":
    main()