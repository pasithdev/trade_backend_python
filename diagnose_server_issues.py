#!/usr/bin/env python3
"""
Server Diagnostic Script for Intermittent 400 Errors
Run this on your production server: 167.71.207.209
"""

import requests
import json
import time
import logging
import os
import subprocess
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_diagnosis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_server_status():
    """Check basic server health"""
    logger.info("=== SERVER HEALTH CHECK ===")
    
    # Check disk space
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        logger.info(f"Disk Usage:\n{result.stdout}")
    except Exception as e:
        logger.error(f"Failed to check disk usage: {e}")
    
    # Check memory usage
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        logger.info(f"Memory Usage:\n{result.stdout}")
    except Exception as e:
        logger.error(f"Failed to check memory usage: {e}")
    
    # Check running processes
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        python_processes = [line for line in result.stdout.split('\n') 
                          if 'python' in line.lower() and 'main.py' in line]
        logger.info(f"Python processes: {len(python_processes)}")
        for proc in python_processes:
            logger.info(f"  {proc}")
    except Exception as e:
        logger.error(f"Failed to check processes: {e}")

def check_application_logs():
    """Check application logs for errors"""
    logger.info("=== APPLICATION LOGS CHECK ===")
    
    log_files = [
        'trading_system.log',
        '/var/log/gunicorn/error.log',
        '/var/log/nginx/error.log',
        'app.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            logger.info(f"Checking {log_file}...")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get last 20 lines
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    for line in recent_lines:
                        if any(keyword in line.lower() for keyword in ['error', '400', 'exception', 'failed']):
                            logger.warning(f"  {line.strip()}")
            except Exception as e:
                logger.error(f"Failed to read {log_file}: {e}")
        else:
            logger.info(f"Log file {log_file} not found")

def test_webhook_endpoints():
    """Test webhook endpoints multiple times to catch intermittent issues"""
    logger.info("=== WEBHOOK ENDPOINT TESTING ===")
    
    base_url = "http://localhost"  # Test locally on server
    
    endpoints = [
        "/api/binance/state-aware-ma-cross-webhook",
        "/api/binance/super-scalper-webhook",
        "/api/binance/target-trend-webhook"
    ]
    
    test_payload = {
        "symbol": "ETHUSDT",
        "action": "buy",
        "balance_percentage": 0.25,
        "leverage": 10,
        "entry": 2456.78
    }
    
    success_count = 0
    total_tests = 0
    
    for endpoint in endpoints:
        logger.info(f"Testing endpoint: {endpoint}")
        
        # Test each endpoint 10 times
        for i in range(10):
            total_tests += 1
            try:
                response = requests.post(
                    f"{base_url}{endpoint}",
                    json=test_payload,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    success_count += 1
                    logger.info(f"  Test {i+1}/10: SUCCESS (200)")
                else:
                    logger.error(f"  Test {i+1}/10: FAILED ({response.status_code}) - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"  Test {i+1}/10: CONNECTION ERROR - {e}")
            
            # Small delay between tests
            time.sleep(0.5)
    
    success_rate = (success_count / total_tests) * 100
    logger.info(f"Overall success rate: {success_rate:.1f}% ({success_count}/{total_tests})")

def check_binance_api_config():
    """Check if Binance API is properly configured"""
    logger.info("=== BINANCE API CONFIGURATION CHECK ===")
    
    try:
        # Test the config endpoint
        response = requests.get("http://localhost/api/binance/status", timeout=5)
        if response.status_code == 200:
            logger.info("Binance API status: OK")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"Binance API status check failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Failed to check Binance API status: {e}")

def check_system_resources():
    """Check system resources during operation"""
    logger.info("=== SYSTEM RESOURCES CHECK ===")
    
    try:
        # Check CPU usage
        result = subprocess.run(['top', '-b', '-n1'], capture_output=True, text=True)
        cpu_lines = [line for line in result.stdout.split('\n')[:10]]
        logger.info("CPU Usage (top 10 processes):")
        for line in cpu_lines:
            logger.info(f"  {line}")
    except Exception as e:
        logger.error(f"Failed to check CPU usage: {e}")

def check_network_connectivity():
    """Check network connectivity and port availability"""
    logger.info("=== NETWORK CONNECTIVITY CHECK ===")
    
    try:
        # Check if the application port is listening
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        listening_ports = [line for line in result.stdout.split('\n') 
                          if ':80 ' in line or ':8000' in line or ':5000' in line]
        
        logger.info("Listening ports:")
        for port in listening_ports:
            logger.info(f"  {port}")
    except Exception as e:
        logger.error(f"Failed to check network ports: {e}")

def main():
    """Run comprehensive server diagnosis"""
    logger.info("Starting comprehensive server diagnosis...")
    logger.info(f"Timestamp: {datetime.now()}")
    
    try:
        check_server_status()
        check_application_logs()
        check_binance_api_config()
        check_system_resources()
        check_network_connectivity()
        test_webhook_endpoints()
        
    except KeyboardInterrupt:
        logger.info("Diagnosis interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during diagnosis: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("=== DIAGNOSIS COMPLETE ===")
    logger.info("Check 'server_diagnosis.log' for detailed results")
    
    # Provide recommendations
    logger.info("\n=== RECOMMENDATIONS ===")
    logger.info("1. Check if multiple Python processes are running (process conflict)")
    logger.info("2. Verify Binance API credentials are properly set")
    logger.info("3. Check for memory/disk space issues")
    logger.info("4. Review application logs for specific error patterns")
    logger.info("5. Consider implementing request rate limiting")
    logger.info("6. Monitor server resources during peak usage")

if __name__ == "__main__":
    main()