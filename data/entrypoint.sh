#!/bin/bash

# Check if DOCKERCONTAINERMANAGER_SERVICE_TYPE is set
if [ -z "$DOCKERCONTAINERMANAGER_SERVICE_TYPE" ]; then
    echo "Error: DOCKERCONTAINERMANAGER_SERVICE_TYPE environment variable is not set"
    echo "Please set DOCKERCONTAINERMANAGER_SERVICE_TYPE to either 'frontend', 'backend', or 'bot'"
    exit 1
fi

case "$DOCKERCONTAINERMANAGER_SERVICE_TYPE" in
    "frontend")
        echo "Starting frontend service..."
        python frontend/app.py
        ;;
    "backend")
        echo "Starting backend service..."
        python backend/main.py
        ;;
    "bot")
        echo "Starting bot service..."
        python bot/bot.py
        ;;
    *)
        echo "Error: Invalid DOCKERCONTAINERMANAGER_SERVICE_TYPE value"
        echo "Please set DOCKERCONTAINERMANAGER_SERVICE_TYPE to either 'frontend', 'backend', or 'bot'"
        exit 1
        ;;
esac 