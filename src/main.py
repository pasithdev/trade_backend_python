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

from flask import Flask, send_from_directory
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

# Enable CORS for all routes
CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(crypto_bp, url_prefix='/api')
app.register_blueprint(tradingview_bp, url_prefix='/api')
app.register_blueprint(binance_bp, url_prefix='/api')
app.register_blueprint(integration_bp, url_prefix='/api')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Development server settings
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('ENVIRONMENT') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
