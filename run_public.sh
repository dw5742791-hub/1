#!/bin/bash
# Public Access Setup for CMS Application
# This script starts the Flask app with a public ngrok tunnel

echo "================================"
echo "CMS - Public Access Setup"
echo "================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-amd64.zip -o ngrok.zip
    unzip -q ngrok.zip
    rm ngrok.zip
    chmod +x ngrok
    echo "✓ ngrok installed"
else
    echo "✓ ngrok found"
fi

echo ""
echo "🚀 Starting Flask application..."
echo ""

# Start Flask app in background
python app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

echo ""
echo "🌐 Creating public tunnel..."
echo ""

# Start ngrok tunnel
./ngrok http 5000

# Cleanup on exit
trap "kill $FLASK_PID" EXIT
