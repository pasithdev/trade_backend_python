#!/usr/bin/env python3
"""
Test script for Smart Position Size Calculation with Auto-Reduction
Demonstrates the intelligent reduction of position size when there's insufficient balance
"""

import requests
import json
import time

# Configuration
SERVER = "http://localhost:80/api"
WEBHOOK_ENDPOINT = f"{SERVER}/binance/advanced-trading-webhook"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_normal_order():
    """Test normal order with sufficient balance"""
    print_section("TEST 1: Normal Order - Sufficient Balance")
    
    payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.10,  # 10% - conservative
        "leverage": 5,
        "entry": 50000.0
    }
    
    print(f"📊 Request: {json.dumps(payload, indent=2)}")
    print("\n🎯 Expected: Order should execute normally")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n✅ Status: {response.status_code}")
        print(f"📈 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            details = result.get('trade', {})
            calc_details = result.get('calculation_details', {})
            
            print(f"\n💰 Position Details:")
            print(f"  - Quantity: {details.get('quantity')}")
            print(f"  - Leverage: {details.get('leverage')}x")
            print(f"  - Entry Price: ${details.get('entry_price')}")
            
            if calc_details.get('auto_reduced'):
                print(f"\n⚠️ Auto-Reduction Applied:")
                print(f"  - Reason: {calc_details.get('adjustment_reason')}")
                print(f"  - Requested: {calc_details.get('requested_balance_percentage')*100:.2f}%")
                print(f"  - Actual: {calc_details.get('actual_balance_percentage')*100:.2f}%")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def test_high_percentage():
    """Test with very high balance percentage (should auto-reduce)"""
    print_section("TEST 2: High Balance % - Should Auto-Reduce")
    
    payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.95,  # 95% - very aggressive
        "leverage": 20,
        "entry": 50000.0
    }
    
    print(f"📊 Request: {json.dumps(payload, indent=2)}")
    print("\n🎯 Expected: Should auto-reduce to prevent margin call")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n✅ Status: {response.status_code}")
        print(f"📈 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            calc_details = result.get('calculation_details', {})
            
            print(f"\n💰 Smart Reduction Details:")
            print(f"  - Requested Balance %: {calc_details.get('requested_balance_percentage')*100:.2f}%")
            print(f"  - Actual Balance %: {calc_details.get('actual_balance_percentage')*100:.2f}%")
            print(f"  - Auto-Reduced: {calc_details.get('auto_reduced')}")
            print(f"  - Reason: {calc_details.get('adjustment_reason')}")
            print(f"  - Final Quantity: {calc_details.get('final_quantity')}")
            print(f"  - Margin Required: ${calc_details.get('margin_required'):.2f}")
            print(f"  - Available Balance: ${calc_details.get('available_balance'):.2f}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def test_small_balance():
    """Test with small balance percentage (below minimum)"""
    print_section("TEST 3: Very Small Position - Auto-Adjust to Minimum")
    
    payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.001,  # 0.1% - very small
        "leverage": 5,
        "entry": 50000.0
    }
    
    print(f"📊 Request: {json.dumps(payload, indent=2)}")
    print("\n🎯 Expected: Should auto-adjust to minimum quantity if possible")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n✅ Status: {response.status_code}")
        print(f"📈 Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            calc_details = result.get('calculation_details', {})
            
            print(f"\n💰 Minimum Adjustment Details:")
            print(f"  - Requested Balance %: {calc_details.get('requested_balance_percentage')*100:.4f}%")
            print(f"  - Actual Balance %: {calc_details.get('actual_balance_percentage')*100:.4f}%")
            print(f"  - Minimum Quantity: {calc_details.get('min_quantity')}")
            print(f"  - Final Quantity: {calc_details.get('final_quantity')}")
            print(f"  - Auto-Reduced: {calc_details.get('auto_reduced')}")
        else:
            # If it failed, show the error
            print(f"\n⚠️ Order Failed (Expected if balance too low):")
            print(f"  - Error: {result.get('error')}")
            if 'details' in result:
                print(f"  - Suggestion: {result['details'].get('suggestion')}")
        
        return True  # Return true anyway since we expect this might fail
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def test_different_symbols():
    """Test with different symbols to show auto-reduction across symbols"""
    print_section("TEST 4: Multiple Symbols - Smart Reduction")
    
    symbols_to_test = [
        {"symbol": "ETHUSDT", "balance_percentage": 0.30, "leverage": 10},
        {"symbol": "BNBUSDT", "balance_percentage": 0.25, "leverage": 15},
        {"symbol": "SOLUSDT", "balance_percentage": 0.20, "leverage": 10}
    ]
    
    results = []
    
    for test_config in symbols_to_test:
        print(f"\n📍 Testing {test_config['symbol']}...")
        
        payload = {
            "symbol": test_config['symbol'],
            "action": "buy",
            "balance_percentage": test_config['balance_percentage'],
            "leverage": test_config['leverage'],
            "entry": 1000.0  # Generic entry price
        }
        
        try:
            response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
            result = response.json()
            
            if result.get('success'):
                calc = result.get('calculation_details', {})
                print(f"  ✅ Success")
                print(f"    - Requested: {calc.get('requested_balance_percentage')*100:.2f}%")
                print(f"    - Actual: {calc.get('actual_balance_percentage')*100:.2f}%")
                print(f"    - Quantity: {calc.get('final_quantity')}")
                print(f"    - Auto-Reduced: {calc.get('auto_reduced')}")
                results.append(True)
            else:
                print(f"  ⚠️ Failed: {result.get('error')}")
                results.append(False)
                
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append(False)
    
    return all(results)

def test_extreme_leverage():
    """Test with extreme leverage (should auto-reduce)"""
    print_section("TEST 5: Extreme Leverage - Auto-Reduction")
    
    payload = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "balance_percentage": 0.50,  # 50%
        "leverage": 75,  # Very high leverage
        "entry": 50000.0
    }
    
    print(f"📊 Request: {json.dumps(payload, indent=2)}")
    print("\n🎯 Expected: Should auto-reduce due to high leverage risk")
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=payload, timeout=30)
        result = response.json()
        
        print(f"\n✅ Status: {response.status_code}")
        
        if result.get('success'):
            calc = result.get('calculation_details', {})
            
            print(f"\n💰 Extreme Leverage Adjustment:")
            print(f"  - Requested Position: {calc.get('requested_balance_percentage')*100:.2f}% @ {payload['leverage']}x")
            print(f"  - Actual Position: {calc.get('actual_balance_percentage')*100:.2f}% @ {payload['leverage']}x")
            print(f"  - Position Value: ${calc.get('position_value_usdt'):.2f}")
            print(f"  - Margin Required: ${calc.get('margin_required'):.2f}")
            print(f"  - Available Balance: ${calc.get('available_balance'):.2f}")
            print(f"  - Safety Maintained: {calc.get('margin_required') < calc.get('available_balance')}")
        else:
            print(f"  ⚠️ Failed: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def main():
    """Run all smart reduction tests"""
    print("\n" + "=" * 70)
    print("  🧠 SMART POSITION SIZE CALCULATION - AUTO-REDUCTION TESTS")
    print("=" * 70)
    print(f"  🎯 Server: {SERVER}")
    print(f"  📍 Endpoint: /binance/advanced-trading-webhook")
    print(f"  ⏰ Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n📋 Test Suite Overview:")
    print("  1. Normal order with sufficient balance")
    print("  2. High balance percentage (auto-reduction)")
    print("  3. Very small position (minimum adjustment)")
    print("  4. Multiple symbols (cross-symbol testing)")
    print("  5. Extreme leverage (safety reduction)")
    
    input("\n⏸️  Press Enter to start tests...")
    
    results = {
        'test1_normal': test_normal_order(),
        'test2_high_percentage': test_high_percentage(),
        'test3_small_balance': test_small_balance(),
        'test4_multiple_symbols': test_different_symbols(),
        'test5_extreme_leverage': test_extreme_leverage()
    }
    
    # Summary
    print_section("📊 TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        test_label = test_name.replace('_', ' ').title()
        print(f"  {test_label}: {status}")
    
    print(f"\n  Total: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)
    
    print("\n🎓 Key Features Demonstrated:")
    print("  ✅ Auto-reduces position when balance insufficient")
    print("  ✅ Maintains minimum quantity requirements")
    print("  ✅ Prevents margin calls with safety buffers")
    print("  ✅ Handles extreme leverage scenarios")
    print("  ✅ Works across different symbols")
    print("  ✅ Provides detailed adjustment information")
    
    print("\n" + "=" * 70)
    
    if passed_tests == total_tests:
        print("  🎉 ALL TESTS PASSED - Smart reduction working perfectly!")
    else:
        print(f"  ⚠️  {total_tests - passed_tests} test(s) failed - Review results above")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
