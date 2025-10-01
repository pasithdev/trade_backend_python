#!/usr/bin/env python3
"""
Remote Server Testing Script for 167.71.207.209
Run this from your local machine to test the production server
"""

import requests
import json
import time
import logging
from datetime import datetime
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SERVER_IP = "167.71.207.209"
BASE_URL = f"http://{SERVER_IP}"

def test_server_connectivity():
    """Test basic server connectivity"""
    logger.info("=== TESTING SERVER CONNECTIVITY ===")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        logger.info(f"Server response: {response.status_code}")
        if response.status_code == 200:
            logger.info("✅ Server is responding")
        else:
            logger.warning(f"⚠️ Server returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Server connectivity failed: {e}")

def extensive_webhook_testing():
    """Run extensive webhook testing to identify intermittent issues"""
    logger.info("=== EXTENSIVE WEBHOOK TESTING ===")
    
    endpoints = [
        "/api/binance/state-aware-ma-cross-webhook",
        "/api/binance/super-scalper-webhook", 
        "/api/binance/target-trend-webhook"
    ]
    
    test_payloads = [
        {
            "symbol": "ETHUSDT",
            "action": "buy",
            "balance_percentage": 0.25,
            "leverage": 10,
            "entry": 2456.78
        },
        {
            "symbol": "BTCUSDT", 
            "action": "buy",
            "balance_percentage": 0.40,
            "leverage": 10,
            "entry": 43000.0
        },
        {
            "symbol": "DOGEUSDT",
            "action": "buy", 
            "balance_percentage": 0.08,
            "leverage": 5,
            "entry": 0.12
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        logger.info(f"\n--- Testing {endpoint} ---")
        
        endpoint_results = {
            'success': 0,
            'failures': [],
            'response_times': [],
            'total_tests': 0
        }
        
        # Test with different payloads and multiple iterations
        for payload in test_payloads:
            symbol = payload['symbol']
            logger.info(f"Testing with {symbol}...")
            
            # Run 20 tests per payload
            for i in range(20):
                endpoint_results['total_tests'] += 1
                start_time = time.time()
                
                try:
                    response = requests.post(
                        f"{BASE_URL}{endpoint}",
                        json=payload,
                        timeout=10,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    response_time = time.time() - start_time
                    endpoint_results['response_times'].append(response_time)
                    
                    if response.status_code == 200:
                        endpoint_results['success'] += 1
                        if i % 5 == 0:  # Log every 5th success
                            logger.info(f"  ✅ Test {i+1}: SUCCESS ({response_time:.2f}s)")
                    else:
                        failure_info = {
                            'test_num': i+1,
                            'symbol': symbol,
                            'status_code': response.status_code,
                            'response': response.text[:200],  # First 200 chars
                            'response_time': response_time
                        }
                        endpoint_results['failures'].append(failure_info)
                        logger.error(f"  ❌ Test {i+1}: FAILED ({response.status_code}) - {response.text[:100]}")
                
                except requests.exceptions.RequestException as e:
                    failure_info = {
                        'test_num': i+1,
                        'symbol': symbol,
                        'error': str(e),
                        'response_time': time.time() - start_time
                    }
                    endpoint_results['failures'].append(failure_info)
                    logger.error(f"  ❌ Test {i+1}: CONNECTION ERROR - {e}")
                
                # Small delay to avoid overwhelming server
                time.sleep(0.2)
        
        results[endpoint] = endpoint_results
        
        # Calculate statistics
        success_rate = (endpoint_results['success'] / endpoint_results['total_tests']) * 100
        avg_response_time = statistics.mean(endpoint_results['response_times']) if endpoint_results['response_times'] else 0
        
        logger.info(f"\n📊 Results for {endpoint}:")
        logger.info(f"   Success Rate: {success_rate:.1f}% ({endpoint_results['success']}/{endpoint_results['total_tests']})")
        logger.info(f"   Average Response Time: {avg_response_time:.2f}s")
        logger.info(f"   Total Failures: {len(endpoint_results['failures'])}")
    
    return results

def analyze_failure_patterns(results):
    """Analyze failure patterns to identify root causes"""
    logger.info("\n=== FAILURE PATTERN ANALYSIS ===")
    
    all_failures = []
    for endpoint, data in results.items():
        all_failures.extend(data['failures'])
    
    if not all_failures:
        logger.info("🎉 No failures detected!")
        return
    
    # Analyze status codes
    status_codes = {}
    for failure in all_failures:
        if 'status_code' in failure:
            code = failure['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
    
    logger.info("📈 Failure Status Codes:")
    for code, count in status_codes.items():
        logger.info(f"   {code}: {count} occurrences")
    
    # Analyze error messages
    error_patterns = {}
    for failure in all_failures:
        if 'response' in failure:
            response = failure['response'].lower()
            if 'minimum' in response and 'quantity' in response:
                error_patterns['minimum_quantity'] = error_patterns.get('minimum_quantity', 0) + 1
            elif 'api' in response and ('not configured' in response or 'credentials' in response):
                error_patterns['api_config'] = error_patterns.get('api_config', 0) + 1
            elif 'balance' in response:
                error_patterns['balance'] = error_patterns.get('balance', 0) + 1
            else:
                error_patterns['other'] = error_patterns.get('other', 0) + 1
    
    logger.info("🔍 Error Patterns:")
    for pattern, count in error_patterns.items():
        logger.info(f"   {pattern}: {count} occurrences")

def provide_recommendations(results):
    """Provide recommendations based on test results"""
    logger.info("\n=== RECOMMENDATIONS ===")
    
    total_tests = sum(data['total_tests'] for data in results.values())
    total_successes = sum(data['success'] for data in results.values())
    overall_success_rate = (total_successes / total_tests) * 100 if total_tests > 0 else 0
    
    logger.info(f"Overall Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate < 50:
        logger.error("🚨 CRITICAL: Very low success rate - major issues detected")
        logger.info("1. Check if the application is running properly on the server")
        logger.info("2. Verify Binance API credentials are configured")
        logger.info("3. Check server logs for application errors")
    elif overall_success_rate < 80:
        logger.warning("⚠️ WARNING: Intermittent issues detected")
        logger.info("1. Implement retry logic in webhook calls")
        logger.info("2. Add request rate limiting")
        logger.info("3. Monitor server resources (CPU, memory)")
        logger.info("4. Check for race conditions in API configuration")
    else:
        logger.info("✅ GOOD: High success rate, minor optimizations possible")
        logger.info("1. Consider adding request caching")
        logger.info("2. Implement health check endpoints")

def main():
    """Run comprehensive remote server testing"""
    logger.info("Starting remote server testing...")
    logger.info(f"Target server: {SERVER_IP}")
    logger.info(f"Timestamp: {datetime.now()}")
    
    # Test basic connectivity
    test_server_connectivity()
    
    # Run extensive webhook testing
    results = extensive_webhook_testing()
    
    # Analyze results
    analyze_failure_patterns(results)
    
    # Provide recommendations
    provide_recommendations(results)
    
    logger.info("\n=== TESTING COMPLETE ===")

if __name__ == "__main__":
    main()