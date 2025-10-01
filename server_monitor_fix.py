#!/usr/bin/env python3
"""
Server Monitoring & Fix Script
Continuously monitors and fixes the intermittent API configuration issue
"""

import requests
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SERVER_IP = "167.71.207.209"
BASE_URL = f"http://{SERVER_IP}"

API_KEY = "M1lUVsQ5VJ8FuuYNdailwDSXsTi1zfVRtbIWb5INCBxoK2ag0voWi9bDZClnTZsJ"
API_SECRET = "bSMHbf1evgubRauqMIRxfZ5iNSuNXGmOXDrBCuv90PkeeDGuN9iYI0mIor8DUBoF"

def configure_api():
    """Configure Binance API credentials"""
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
            logger.info("✅ API configured successfully")
            return True
        else:
            logger.error(f"❌ API config failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ API config error: {e}")
        return False

def test_webhook():
    """Test webhook functionality"""
    test_payload = {
        "symbol": "ETHUSDT",
        "action": "buy",
        "balance_percentage": 0.50,  # 50% to ensure minimum requirements
        "leverage": 10,
        "entry": 2456.78
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/binance/state-aware-ma-cross-webhook",
            json=test_payload,
            timeout=15
        )
        
        if response.status_code == 200:
            logger.info("✅ Webhook test successful")
            return True, "success"
        else:
            error_text = response.text.lower()
            if "not configured" in error_text:
                logger.warning("⚠️ API credentials lost - needs reconfiguration")
                return False, "api_config_lost"
            elif "minimum" in error_text or "notional" in error_text:
                logger.warning("⚠️ Position size too small")
                return False, "position_size"
            else:
                logger.error(f"❌ Webhook failed: {response.status_code} - {response.text}")
                return False, "other_error"
                
    except Exception as e:
        logger.error(f"❌ Webhook test error: {e}")
        return False, "connection_error"

def monitoring_cycle():
    """Run one monitoring cycle"""
    logger.info("🔍 Running monitoring cycle...")
    
    # Test webhook
    success, error_type = test_webhook()
    
    if success:
        return True
    
    # Handle different error types
    if error_type == "api_config_lost":
        logger.info("🔧 Reconfiguring API credentials...")
        if configure_api():
            time.sleep(2)
            # Test again after reconfiguration
            success, _ = test_webhook()
            return success
    
    return False

def run_continuous_monitoring(duration_minutes=30):
    """Run continuous monitoring for specified duration"""
    logger.info(f"🚀 Starting continuous monitoring for {duration_minutes} minutes...")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    success_count = 0
    total_cycles = 0
    api_reconfigs = 0
    
    # Initial API configuration
    logger.info("🔧 Initial API configuration...")
    configure_api()
    time.sleep(3)
    
    while time.time() < end_time:
        total_cycles += 1
        
        success = monitoring_cycle()
        if success:
            success_count += 1
        else:
            api_reconfigs += 1
        
        # Log progress every 10 cycles
        if total_cycles % 10 == 0:
            success_rate = (success_count / total_cycles) * 100
            logger.info(f"📊 Progress: {success_rate:.1f}% success rate ({success_count}/{total_cycles})")
        
        # Wait before next cycle
        time.sleep(30)  # Test every 30 seconds
    
    # Final report
    success_rate = (success_count / total_cycles) * 100
    logger.info(f"\n📈 MONITORING COMPLETE")
    logger.info(f"   Duration: {duration_minutes} minutes")
    logger.info(f"   Total Tests: {total_cycles}")
    logger.info(f"   Success Rate: {success_rate:.1f}% ({success_count}/{total_cycles})")
    logger.info(f"   API Reconfigurations: {api_reconfigs}")
    
    return success_rate

def run_quick_fix():
    """Run a quick fix cycle"""
    logger.info("🚨 RUNNING QUICK FIX...")
    
    # Step 1: Configure API
    logger.info("1. Configuring API...")
    configure_api()
    time.sleep(2)
    
    # Step 2: Test with multiple position sizes
    test_configs = [
        {"symbol": "ETHUSDT", "balance_percentage": 0.50, "entry": 2456.78},
        {"symbol": "BTCUSDT", "balance_percentage": 0.80, "entry": 43000.0},
        {"symbol": "DOGEUSDT", "balance_percentage": 0.30, "entry": 0.12}
    ]
    
    logger.info("2. Testing multiple configurations...")
    success_count = 0
    
    for config in test_configs:
        test_payload = {
            "symbol": config["symbol"],
            "action": "buy",
            "balance_percentage": config["balance_percentage"],
            "leverage": 10,
            "entry": config["entry"]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/state-aware-ma-cross-webhook",
                json=test_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ {config['symbol']}: SUCCESS")
                success_count += 1
            else:
                logger.error(f"❌ {config['symbol']}: FAILED - {response.text[:100]}")
                
        except Exception as e:
            logger.error(f"❌ {config['symbol']}: ERROR - {e}")
        
        time.sleep(1)
    
    success_rate = (success_count / len(test_configs)) * 100
    logger.info(f"📊 Quick Fix Results: {success_rate:.1f}% success rate")
    
    return success_rate >= 66.7  # 2 out of 3 should work

def main():
    """Main function"""
    print("🚨 SERVER MONITORING & FIX TOOL")
    print("================================")
    print("1. Quick Fix (immediate)")
    print("2. Continuous Monitoring (30 minutes)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        if run_quick_fix():
            print("\n🎉 Quick fix successful! Server should be stable now.")
        else:
            print("\n⚠️ Quick fix had limited success. Consider continuous monitoring.")
    
    elif choice == "2":
        success_rate = run_continuous_monitoring(30)
        if success_rate >= 80:
            print("\n🎉 Server is stable!")
        else:
            print(f"\n⚠️ Server stability issues detected ({success_rate:.1f}% success)")
    
    elif choice == "3":
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    # For immediate fixing, run quick fix
    run_quick_fix()