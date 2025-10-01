import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Skip Xcode license check in production (only needed on macOS)
if os.getenv('ENVIRONMENT') != 'production':
    import subprocess
    try:
        subprocess.run(['xcodebuild', '-checkFirstLaunchStatus'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Skip if xcodebuild is not available (e.g., on Linux servers)
        pass

# Configure logging for production and development
log_level = logging.DEBUG if os.getenv('ENVIRONMENT') != 'production' else logging.INFO
log_handlers = [logging.StreamHandler()]

# Only add file handler in development or if writable directory exists
if os.getenv('ENVIRONMENT') != 'production':
    try:
        log_handlers.append(logging.FileHandler('trading_system.log'))
    except (PermissionError, OSError):
        pass  # Skip file logging if not writable

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

from flask import Flask, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.crypto import crypto_bp
from src.routes.tradingview import tradingview_bp
from src.routes.binance_trading import binance_bp
from src.routes.integration import integration_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Enable CORS for all routes with proper configuration
CORS(app, 
     origins=["*"],  # Allow all origins in production (you can restrict this later)
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(crypto_bp, url_prefix='/api')
app.register_blueprint(tradingview_bp, url_prefix='/api')
app.register_blueprint(binance_bp, url_prefix='/api')
app.register_blueprint(integration_bp, url_prefix='/api')

# Database configuration
database_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
# Ensure database directory exists
os.makedirs(os.path.dirname(database_path), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        logging.info("Database initialized successfully")
        logging.info(f"App running in {os.getenv('ENVIRONMENT', 'development')} mode")
        logging.info(f"Static folder: {app.static_folder}")
        logging.info(f"App secret key configured: {'Yes' if app.config.get('SECRET_KEY') else 'No'}")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        # Don't fail the app startup if database init fails
        pass

# Health check endpoint for DigitalOcean App Platform
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'Trading backend is running',
        'timestamp': logging.Formatter().formatTime(logging.LogRecord(
            'healthcheck', logging.INFO, '', 0, '', (), None
        )),
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'port': os.getenv('PORT', '80')
    }), 200

# API status endpoint
@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'online',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'version': '1.0.0',
        'port': os.getenv('PORT', '80'),
        'workers': os.getenv('WEB_CONCURRENCY', '2')
    }), 200

# Root endpoint - serves the main page or API info
@app.route('/')
def root():
    static_folder_path = app.static_folder
    index_path = os.path.join(static_folder_path or "", 'index.html')

    if static_folder_path and os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as index_file:
                html_content = index_file.read()
            response = app.make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
        except OSError as exc:
            logging.error(f"Failed to load index.html: {exc}")

    # Return API information if no static files or loading failed
    return jsonify(
        {
            'message': 'Trade Backend Python API',
            'status': 'online',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'api_status': '/api/status',
                'users': '/api/users',
                'crypto': '/api/crypto',
                'tradingview': '/api/tradingview',
                'binance': '/api/binance',
                'integration': '/api/integration'
            }
        }
    ), 200

@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return app.send_static_file(path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return app.send_static_file('index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Development server settings
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('ENVIRONMENT') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
