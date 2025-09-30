#!/bin/bash

# Startup script for DigitalOcean App Platform deployment
echo "Starting Trade Backend Python application..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENVIRONMENT=production

# Create necessary directories
mkdir -p src/database
mkdir -p logs

# Set proper permissions (if needed)
chmod -R 755 src/

# Log startup information
echo "Environment: $ENVIRONMENT"
echo "Python path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Check if all required files exist
if [ ! -f "src/main.py" ]; then
    echo "ERROR: src/main.py not found!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

echo "All required files found. Starting application with gunicorn..."

# Start the application
exec gunicorn -c gunicorn.conf.py src.main:app
