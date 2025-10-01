#!/usr/bin/env python3
"""
Test Super Scalper Webhook Fix
Tests the fixed Super Scalper webhook endpoint
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SERVER_IP = "167.71.207.209"
BASE_URL = f"http://{SERVER_IP}"

def test_super_scalper_webhook():
    """Test the Super Scalper webhook with various payloads"""
    logger.info("🧪 TESTING SUPER SCALPER WEBHOOK FIX")
    
    # Test configurations
    test_configs = [
        {
            "name": "ETHUSDT - High Balance",
            "payload": {
                "symbol": "ETHUSDT",
                "action": "buy",
                "balance_percentage": 0.50,  # 50% for higher position value
                "leverage": 10,
                "entry": 2456.78,
                "signal_strength": "strong",
                "risk_level": "medium"
            }
        },
        {
            "name": "BTCUSDT - Max Balance", 
            "payload": {
                "symbol": "BTCUSDT",
                "action": "buy",
                "balance_percentage": 0.80,  # 80% for BTC
                "leverage": 5,
                "entry": 43000.0,
                "signal_strength": "very_strong",
                "risk_level": "low"
            }
        },
        {
            "name": "DOGEUSDT - Medium Balance",
            "payload": {
                "symbol": "DOGEUSDT", 
                "action": "buy",
                "balance_percentage": 0.25,  # 25% for DOGE
                "leverage": 10,
                "entry": 0.12,
                "signal_strength": "medium",
                "risk_level": "high"
            }
        },
        {
            "name": "SOLUSDT - Standard",
            "payload": {
                "symbol": "SOLUSDT",
                "action": "buy", 
                "balance_percentage": 0.30,
                "leverage": 10,
                "entry": 142.50,
                "signal_strength": "strong",
                "risk_level": "medium"
            }
        }
    ]
    
    success_count = 0
    total_tests = len(test_configs)
    
    for config in test_configs:
        name = config["name"]
        payload = config["payload"]
        
        logger.info(f"\n--- Testing {name} ---")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/super-scalper-webhook",
                json=payload,
                timeout=15,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ {name}: SUCCESS!")
                result = response.json()
                if 'details' in result:
                    details = result['details']
                    logger.info(f"   Position: {details.get('calculated_quantity', 'N/A')} {payload['symbol']}")
                    logger.info(f"   Value: ${details.get('position_value', 'N/A')}")
                success_count += 1
            else:
                logger.error(f"❌ {name}: FAILED ({response.status_code})")
                error_text = response.text
                
                # Check if it's the old error
                if "Failed to get symbol requirements" in error_text:
                    logger.error(f"   CRITICAL: Still getting symbol requirements error!")
                elif "minNotional" in error_text:
                    logger.error(f"   CRITICAL: minNotional error still occurring!")
                else:
                    logger.error(f"   Different error: {error_text[:200]}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {name}: CONNECTION ERROR - {e}")
        
        time.sleep(1)  # Small delay between tests
    
    # Results summary
    success_rate = (success_count / total_tests) * 100
    logger.info(f"\n📊 SUPER SCALPER TEST RESULTS:")
    logger.info(f"   Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    if success_rate >= 75:
        logger.info("🎉 EXCELLENT: Super Scalper webhook is working well!")
    elif success_rate >= 50:
        logger.info("✅ GOOD: Super Scalper webhook is mostly functional")
    elif success_rate > 0:
        logger.info("⚠️ PARTIAL: Some Super Scalper tests working, needs more fixes")
    else:
        logger.error("❌ FAILED: Super Scalper webhook still not working")
    
    return success_rate

def test_symbol_requirements_directly():
    """Test the symbol requirements endpoint directly"""
    logger.info("\n🔍 TESTING SYMBOL REQUIREMENTS DIRECTLY")
    
    test_symbols = ["ETHUSDT", "BTCUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT"]
    
    for symbol in test_symbols:
        try:
            # Test if there's a direct endpoint for symbol requirements
            response = requests.get(f"{BASE_URL}/api/binance/symbol-info/{symbol}", timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ {symbol}: Symbol info available")
            else:
                logger.info(f"⚠️ {symbol}: No direct symbol info endpoint")
        
        except Exception as e:
            logger.info(f"⚠️ {symbol}: {e}")

def main():
    """Run comprehensive Super Scalper webhook testing"""
    logger.info("🚀 SUPER SCALPER WEBHOOK FIX TESTING")
    logger.info("=" * 50)
    
    # Test symbol requirements directly first
    test_symbol_requirements_directly()
    
    # Test the webhook
    success_rate = test_super_scalper_webhook()
    
    logger.info("\n" + "=" * 50)
    logger.info("🏁 TESTING COMPLETE")
    
    if success_rate >= 75:
        logger.info("✅ Super Scalper webhook fix appears successful!")
        logger.info("📈 Ready for production use")
    else:
        logger.info("⚠️ Super Scalper webhook needs additional fixes")
        logger.info("🔧 Check server logs for more details")

if __name__ == "__main__":
    main()