#!/usr/bin/env python3

import requests
import json
import time

def test_symbol_compatibility():
    """Test webhook with various crypto symbols to ensure minimum quantity requirements are met"""
    base_url = "http://167.71.207.209/api"
    
    # Configure API credentials first
    config_payload = {
        "api_key": "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ",
        "api_secret": "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF",
        "testnet": False
    }
    
    print("Configuring API credentials...")
    try:
        response = requests.post(f"{base_url}/binance/config", json=config_payload)
        if response.status_code == 200:
            print("✅ API configured successfully")
        else:
            print("❌ API configuration failed")
            return
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    time.sleep(2)
    
    # Test symbols with their appropriate balance percentages
    test_symbols = [
        # Major pairs (higher minimum values)
        {"symbol": "BTCUSDT", "balance_percentage": 0.40, "expected_min_qty": 0.001},
        {"symbol": "ETHUSDT", "balance_percentage": 0.20, "expected_min_qty": 0.01},
        {"symbol": "BNBUSDT", "balance_percentage": 0.15, "expected_min_qty": 0.01},
        
        # Mid-cap pairs (moderate minimum values)
        {"symbol": "ADAUSDT", "balance_percentage": 0.10, "expected_min_qty": 1.0},
        {"symbol": "SOLUSDT", "balance_percentage": 0.15, "expected_min_qty": 0.1},
        {"symbol": "DOTUSDT", "balance_percentage": 0.10, "expected_min_qty": 0.1},
        {"symbol": "LINKUSDT", "balance_percentage": 0.10, "expected_min_qty": 0.01},
        
        # Lower-cap pairs (smaller minimum values)
        {"symbol": "DOGEUSDT", "balance_percentage": 0.05, "expected_min_qty": 10.0},
        {"symbol": "XRPUSDT", "balance_percentage": 0.05, "expected_min_qty": 1.0},
        {"symbol": "MATICUSDT", "balance_percentage": 0.05, "expected_min_qty": 1.0},
    ]
    
    print("\n" + "=" * 70)
    print("TESTING SYMBOL COMPATIBILITY WITH ADAPTIVE BALANCE PERCENTAGES")
    print("=" * 70)
    
    successful_symbols = []
    failed_symbols = []
    
    for test_case in test_symbols:
        symbol = test_case["symbol"]
        balance_pct = test_case["balance_percentage"]
        expected_min = test_case["expected_min_qty"]
        
        # Create webhook payload
        webhook_payload = {
            "symbol": symbol,
            "action": "buy",
            "balance_percentage": balance_pct,
            "leverage": 10,
            "entry": 1.0  # Placeholder entry price
        }
        
        print(f"\nTesting {symbol}:")
        print(f"  Balance %: {balance_pct*100}%")
        print(f"  Expected Min Qty: {expected_min}")
        print("-" * 50)
        
        try:
            response = requests.post(f"{base_url}/binance/state-aware-ma-cross-webhook", 
                                   json=webhook_payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {symbol} - SUCCESS")
                response_data = response.json()
                
                if 'calculation_details' in response_data:
                    details = response_data['calculation_details']
                    calculated_qty = details.get('final_quantity', 'N/A')
                    position_value = details.get('position_value_usdt', 'N/A')
                    current_price = details.get('current_price', 'N/A')
                    
                    print(f"  ✓ Calculated Quantity: {calculated_qty}")
                    print(f"  ✓ Position Value: ${position_value}")
                    print(f"  ✓ Current Price: ${current_price}")
                    
                    successful_symbols.append({
                        'symbol': symbol,
                        'balance_pct': balance_pct,
                        'calculated_qty': calculated_qty,
                        'position_value': position_value
                    })
                else:
                    print(f"  ⚠️ Success but no calculation details")
                    successful_symbols.append({'symbol': symbol, 'balance_pct': balance_pct})
                    
            else:
                print(f"❌ {symbol} - FAILED")
                response_data = response.json()
                error_msg = response_data.get('error', 'Unknown error')
                print(f"  Error: {error_msg}")
                
                # Check if it's a minimum quantity issue
                if 'minimum' in error_msg.lower() or 'quantity' in error_msg.lower():
                    if 'details' in response_data:
                        details = response_data['details']
                        min_balance_needed = details.get('minimum_balance_percentage', 0) * 100
                        print(f"  💡 Suggested minimum balance: {min_balance_needed:.1f}%")
                
                failed_symbols.append({
                    'symbol': symbol,
                    'balance_pct': balance_pct,
                    'error': error_msg
                })
                
        except requests.exceptions.Timeout:
            print(f"❌ {symbol} - TIMEOUT")
            failed_symbols.append({'symbol': symbol, 'error': 'Timeout'})
        except Exception as e:
            print(f"❌ {symbol} - ERROR: {e}")
            failed_symbols.append({'symbol': symbol, 'error': str(e)})
        
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 70)
    print("COMPATIBILITY TEST SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ SUCCESSFUL SYMBOLS ({len(successful_symbols)}):")
    for result in successful_symbols:
        balance_pct = result['balance_pct'] * 100
        print(f"  • {result['symbol']} - {balance_pct}% balance")
        if 'calculated_qty' in result:
            print(f"    Qty: {result['calculated_qty']}, Value: ${result['position_value']}")
    
    print(f"\n❌ FAILED SYMBOLS ({len(failed_symbols)}):")
    for result in failed_symbols:
        balance_pct = result['balance_pct'] * 100
        print(f"  • {result['symbol']} - {balance_pct}% balance")
        print(f"    Error: {result['error']}")
    
    # Success rate
    total_tests = len(successful_symbols) + len(failed_symbols)
    success_rate = (len(successful_symbols) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 SUCCESS RATE: {success_rate:.1f}% ({len(successful_symbols)}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 EXCELLENT: Most symbols are working correctly!")
    elif success_rate >= 60:
        print("👍 GOOD: Majority of symbols are working, minor adjustments needed")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Several symbols require balance percentage adjustments")

def test_close_functionality():
    """Test close functionality across different symbols"""
    print("\n" + "=" * 70)
    print("TESTING CLOSE FUNCTIONALITY")
    print("=" * 70)
    
    close_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOGEUSDT"]
    
    for symbol in close_symbols:
        close_payload = {
            "symbol": symbol,
            "action": "close",  
            "balance_percentage": 0.20,
            "leverage": 10,
            "entry": 1.0
        }
        
        print(f"\nTesting close for {symbol}...")
        
        try:
            response = requests.post("http://167.71.207.209/api/binance/state-aware-ma-cross-webhook",
                                   json=close_payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {symbol} close - SUCCESS")
            else:
                print(f"❌ {symbol} close - FAILED")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"❌ {symbol} close - ERROR: {e}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE SYMBOL COMPATIBILITY TEST")
    print("Testing adaptive balance percentage system...")
    print()
    
    test_symbol_compatibility()
    test_close_functionality()
    
    print("\n" + "=" * 70)
    print("✅ TESTING COMPLETE!")
    print("=" * 70)
    print("\n💡 Tips for Pine Script configuration:")
    print("  • Use 10-15% base balance for most altcoins")
    print("  • Use 30-50% base balance for BTC/ETH")
    print("  • Enable debug table to see adaptive calculations")
    print("  • Test with paper trading first!")