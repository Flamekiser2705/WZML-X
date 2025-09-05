#!/bin/bash

# Auth Bot Startup Script
echo "🔐 Starting WZML-X Auth Bot..."

# Check if Python 3.9+ is installed
python_version=$(python3 -c "import sys; print(sys.version_info.major, sys.version_info.minor)")
if [[ $python_version < "3 9" ]]; then
    echo "❌ Python 3.9+ is required"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check if config.env exists
if [ ! -f "config.env" ]; then
    echo "❌ config.env file not found!"
    echo "Please copy config.env.sample to config.env and configure it"
    exit 1
fi

# Start the bot
echo "🚀 Starting Auth Bot..."
python3 -m bot
