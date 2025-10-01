#!/usr/bin/env python3

import requests
import json
import time

def test_api_endpoints():
    base_url = "http://167.71.207.209/api"
    
    # Test 1: Configure API
    config_payload = {
        "api_key": "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ",
        "api_secret": "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF",
        "testnet": False
    }
    
    print("=== STEP 1: Configure Binance API ===")
    try:
        response = requests.post(f"{base_url}/binance/config", json=config_payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Wait a moment for configuration to take effect
    time.sleep(2)
    
    # Test 2: Check account info
    print("=== STEP 2: Check Account Info ===")
    try:
        response = requests.get(f"{base_url}/binance/account")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Try state-aware webhook
    webhook_payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.01,
        "leverage": 10,
        "entry": 43000
    }
    
    print("=== STEP 3: Test State-Aware Webhook ===")
    try:
        response = requests.post(f"{base_url}/binance/state-aware-ma-cross-webhook", json=webhook_payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Try integration webhook (this one worked)
    print("=== STEP 4: Test Integration Endpoint ===")
    integration_payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "quantity": 0.001,
        "balance_percentage": 0.01
    }
    
    try:
        response = requests.post(f"{base_url}/integration/tradingview-to-binance", json=integration_payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()