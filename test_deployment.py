#!/usr/bin/env python3
"""
Test script to verify deployment readiness for DigitalOcean App Platform
"""

import os
import sys
import importlib.util

def test_imports():
    """Test that all required modules can be imported"""
    required_modules = [
        'flask',
        'flask_cors', 
        'flask_sqlalchemy',
        'binance',
        'requests',
        'gunicorn'
    ]
    
    print("🧪 Testing Python imports...")
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    return True

def test_app_startup():
    """Test that the Flask app can start"""
    print("\n🚀 Testing Flask app startup...")
    try:
        # Set production environment
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['PORT'] = '8080'
        
        # Import the app
        from src.main import app
        
        # Test app configuration
        with app.app_context():
            print(f"✅ App created successfully")
            print(f"✅ Secret key configured: {'***' if app.config['SECRET_KEY'] else 'None'}")
            print(f"✅ Environment: {os.getenv('ENVIRONMENT')}")
            print(f"✅ Port: {os.getenv('PORT')}")
            
        return True
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return False

def test_files():
    """Test that all deployment files exist"""
    print("\n📁 Testing deployment files...")
    required_files = [
        'requirements.txt',
        'runtime.txt', 
        'Procfile',
        'app.yaml',
        'DEPLOYMENT_GUIDE.md',
        'src/main.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            return False
    return True

def main():
    """Run all tests"""
    print("🎯 DigitalOcean App Platform Deployment Test")
    print("=" * 50)
    
    tests = [
        test_files,
        test_imports,
        test_app_startup
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Ready for DigitalOcean deployment!")
        print("\n📋 Next Steps:")
        print("1. Push code to GitHub repository")
        print("2. Create app on DigitalOcean App Platform")
        print("3. Connect GitHub repository")
        print("4. Set environment variables")
        print("5. Deploy!")
        print("\n📖 See DEPLOYMENT_GUIDE.md for detailed instructions")
    else:
        print("❌ Some tests failed. Please fix the issues before deploying.")
        sys.exit(1)

if __name__ == '__main__':
    main()
