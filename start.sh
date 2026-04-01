#!/bin/bash

# IntermodalFreightEnv Frontend & Backend Startup Script
# Starts both services in separate terminal windows/tabs

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Starting IntermodalFreightEnv..."
echo ""

# Check if using Docker Compose
if command -v docker-compose &> /dev/null; then
    read -p "Use Docker Compose? (y/n) [default: y]: " use_docker
    use_docker=${use_docker:-y}
    
    if [[ $use_docker == "y" ]]; then
        echo "🐳 Starting with Docker Compose..."
        docker-compose up
        exit 0
    fi
fi

# Manual startup
echo "📋 Starting services manually..."
echo ""

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use (backend likely running)"
else
    echo "▶️  Starting Backend (port 8000)..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 2
fi

# Check if frontend is already running
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8501 is already in use (frontend likely running)"
else
    echo "▶️  Starting Frontend (port 8501)..."
    
    # Create a new terminal tab/window depending on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open -a Terminal <<EOF
cd "$PROJECT_DIR"
streamlit run frontend/dashboard.py
EOF
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - try common terminal emulators
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$PROJECT_DIR' && streamlit run frontend/dashboard.py"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$PROJECT_DIR' && streamlit run frontend/dashboard.py" &
        else
            # Fallback: run in same terminal
            echo "⚠️  Couldn't open new terminal, running frontend in background..."
            streamlit run frontend/dashboard.py --server.port=8501 &
        fi
    fi
fi

echo ""
echo "✅ Services starting..."
echo ""
echo "📊 Frontend: http://localhost:8501"
echo "🔌 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
