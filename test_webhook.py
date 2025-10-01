#!/usr/bin/env python3

import requests
import json

# Test the state-aware MA cross webhook
def test_state_aware_webhook():
    url = "http://167.71.207.209/api/binance/state-aware-ma-cross-webhook"
    
    payload = {
        "symbol": "BTCUSDT",
        "action": "buy", 
        "balance_percentage": 0.01,  # 1% of balance
        "leverage": 10,
        "entry": 43000
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"Testing webhook: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook is working!")
        else:
            print("❌ ERROR: Webhook returned error")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")

if __name__ == "__main__":
    test_state_aware_webhook()