#!/bin/bash

# AI Ready CRM Launcher - Salesforce Benchmark Mode
echo "🚀 Initializing AI Ready CRM..."

# 1. Port Check
PORT=8000
PID=$(lsof -ti:$PORT)

if [ ! -z "$PID" ]; then
    echo "⚠️ Port $PORT is already in use by process $PID."
    echo "🔄 Restarting server..."
    kill -9 $PID
    sleep 1
fi

# Start uvicorn from the project root
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"
export PYTHONPATH=.:../skills:$PYTHONPATH

uvicorn backend.app.main:app --host 127.0.0.1 --port $PORT > crm.log 2>&1 &
SERVER_PID=$!

# 3. Wait for startup
echo "⏳ Waiting for server to wake up..."
for i in {1..5}; do
    if curl -s http://127.0.0.1:$PORT > /dev/null; then
        break
    fi
    sleep 1
done

# 4. Open Browser
echo "🌐 Opening Salesforce-aligned Dashboard at http://127.0.0.1:$PORT"
open "http://127.0.0.1:$PORT"

echo "💡 CRM is live. Press Ctrl+C to shutdown."
wait $SERVER_PID
