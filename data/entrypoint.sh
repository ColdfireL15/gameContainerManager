#!/bin/sh

# Check if DOCKERCONTAINERMANAGER_SERVICE_TYPE is set
if [ -z "$DOCKERCONTAINERMANAGER_SERVICE_TYPE" ]; then
    echo "Error: DOCKERCONTAINERMANAGER_SERVICE_TYPE environment variable is not set"
    echo "Please set DOCKERCONTAINERMANAGER_SERVICE_TYPE to either 'frontend', 'backend', or 'bot'"
    exit 1
fi

case "$DOCKERCONTAINERMANAGER_SERVICE_TYPE" in
    "frontend")
        echo "Starting frontend service with Gunicorn..."
        gunicorn --bind 0.0.0.0:5000 --access-logfile - --error-logfile - "frontend.app:app"
        ;;
    "backend")
        echo "Starting backend service with Gunicorn and Uvicorn..."
        gunicorn --bind 0.0.0.0:5000 --access-logfile - --error-logfile - "backend.main:app"
        ;;
    "bot")
        echo "Starting bot service with Gunicorn and Uvicorn..."
        gunicorn --bind 0.0.0.0:5000 --worker-class uvicorn.workers.UvicornWorker --access-logfile - --error-logfile - "bot.bot:app"
        ;;
    *)
        echo "Error: Invalid DOCKERCONTAINERMANAGER_SERVICE_TYPE value"
        echo "Please set DOCKERCONTAINERMANAGER_SERVICE_TYPE to either 'frontend', 'backend', or 'bot'"
        exit 1
        ;;
esac
