import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes - adjust based on environment
if os.getenv('ENVIRONMENT') == 'production':
    workers = int(os.getenv('GUNICORN_WORKERS', min(multiprocessing.cpu_count() * 2 + 1, 4)))
else:
    workers = 2

worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = 100

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'trade_backend_python'

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in the future)
keyfile = None
certfile = None

# Preload application for better memory usage
preload_app = True

# Enable automatic worker restarts
reload = False

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
