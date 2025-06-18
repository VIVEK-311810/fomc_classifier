#!/bin/bash

# Start FastAPI backend in the background
echo "Starting FastAPI backend..."
cd /app && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start Streamlit frontend in the foreground
echo "Starting Streamlit frontend..."
cd /app && streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
FRONTEND_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for either process to exit
wait -n

# If we get here, one process has exited, so clean up
cleanup

