#!/bin/bash

case "$1" in
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
        echo "Usage: docker run <image> [frontend|backend|bot]"
        echo "Please specify either 'frontend' or 'backend' or 'bot'"
        exit 1
        ;;
esac 