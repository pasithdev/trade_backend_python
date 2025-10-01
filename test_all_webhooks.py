#!/usr/bin/env python3

import requests
import json
import time

def test_webhook_endpoints():
    """Test all webhook endpoints with the new payload format"""
    base_url = "http://167.71.207.209/api"
    
    # Test payload in the new format
    webhook_payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.50,
        "leverage": 10,
        "entry": 43000
    }
    
    webhook_endpoints = [
        "/binance/state-aware-ma-cross-webhook",
        "/binance/smart-webhook", 
        "/binance/super-scalper-webhook",
        "/binance/target-trend-webhook",
        "/integration/tradingview-to-binance"
    ]
    
    print("=" * 60)
    print("TESTING ALL WEBHOOK ENDPOINTS WITH NEW PAYLOAD FORMAT")
    print("=" * 60)
    print(f"Test Payload: {json.dumps(webhook_payload, indent=2)}")
    print()
    
    for endpoint in webhook_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing: {endpoint}")
        print("-" * 40)
        
        try:
            response = requests.post(url, json=webhook_payload, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS")
                response_data = response.json()
                if 'trade' in response_data:
                    trade_info = response_data['trade']
                    print(f"Trade Details: {json.dumps(trade_info, indent=2)}")
            else:
                print("❌ ERROR")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT - Request took too long")
        except requests.exceptions.RequestException as e:
            print(f"❌ REQUEST ERROR: {e}")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            
        print()
        time.sleep(1)  # Rate limiting
    
    # Test close action
    print("=" * 60)
    print("TESTING CLOSE ACTION")
    print("=" * 60)
    
    close_payload = {
        "symbol": "BTCUSDT",
        "action": "close",
        "balance_percentage": 0.50,
        "leverage": 10,
        "entry": 43000
    }
    
    print(f"Close Payload: {json.dumps(close_payload, indent=2)}")
    print()
    
    for endpoint in ["/binance/state-aware-ma-cross-webhook", "/binance/smart-webhook"]:
        url = f"{base_url}{endpoint}"
        print(f"Testing Close: {endpoint}")
        print("-" * 40)
        
        try:
            response = requests.post(url, json=close_payload, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ CLOSE SUCCESS")
            else:
                print("❌ CLOSE ERROR")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            
        print()
        time.sleep(1)

def test_minimum_balance_requirements():
    """Test different balance percentages to understand minimum requirements"""
    base_url = "http://167.71.207.209/api"
    endpoint = "/binance/state-aware-ma-cross-webhook"
    
    balance_percentages = [0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50]
    
    print("=" * 60)
    print("TESTING MINIMUM BALANCE REQUIREMENTS")
    print("=" * 60)
    
    for balance_pct in balance_percentages:
        test_payload = {
            "symbol": "BTCUSDT",
            "action": "buy", 
            "balance_percentage": balance_pct,
            "leverage": 10,
            "entry": 43000
        }
        
        print(f"Testing {balance_pct*100}% balance...")
        
        try:
            response = requests.post(f"{base_url}{endpoint}", json=test_payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {balance_pct*100}% - SUCCESS")
                response_data = response.json()
                if 'calculation_details' in response_data:
                    details = response_data['calculation_details']
                    print(f"   Position Value: ${details.get('position_value_usdt', 'N/A')}")
                    print(f"   Calculated Quantity: {details.get('final_quantity', 'N/A')}")
            else:
                print(f"❌ {balance_pct*100}% - FAILED")
                response_data = response.json()
                if 'details' in response_data:
                    details = response_data['details']
                    min_pct = details.get('minimum_balance_percentage', 0) * 100
                    print(f"   Minimum required: {min_pct:.1f}%")
                    
        except Exception as e:
            print(f"❌ {balance_pct*100}% - ERROR: {e}")
            
        print()
        time.sleep(0.5)

if __name__ == "__main__":
    print("COMPREHENSIVE WEBHOOK TESTING")
    print("=" * 60)
    
    # First configure API credentials
    config_payload = {
        "api_key": "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ",
        "api_secret": "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF",
        "testnet": False
    }
    
    print("Configuring API credentials...")
    try:
        response = requests.post("http://167.71.207.209/api/binance/config", json=config_payload)
        if response.status_code == 200:
            print("✅ API configured successfully")
        else:
            print("❌ API configuration failed")
            print(response.text)
            exit(1)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
    
    print()
    time.sleep(2)
    
    # Run tests
    test_webhook_endpoints()
    test_minimum_balance_requirements()
    
    print("=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)