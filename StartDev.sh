#!/bin/bash
# StartDev.sh - Unified development startup script for Linux/Mac
# Usage: ./StartDev.sh

echo ""
echo "🚀 Starting Agent Interface..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get script directory
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Check prerequisites
echo ""
echo "[1/4] Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+ and try again."
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm not found. Please install Node.js and try again."
    exit 1
fi
echo "✓ Prerequisites OK"

# Check Ollama and pull required models
echo ""
echo "[1.5/4] Checking Ollama models..."
if command -v ollama &> /dev/null; then
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running"
        
        # Pull required models if not present
        MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
        
        if ! echo "$MODELS" | grep -q "llama3.2"; then
            echo "Pulling llama3.2 model (this may take a few minutes)..."
            ollama pull llama3.2
        else
            echo "✓ llama3.2 model ready"
        fi
        
        if ! echo "$MODELS" | grep -q "nomic-embed-text"; then
            echo "Pulling nomic-embed-text model (for vector embeddings)..."
            ollama pull nomic-embed-text
        else
            echo "✓ nomic-embed-text model ready"
        fi
    else
        echo "⚠️  Ollama not running. Start it with: ollama serve"
        echo "   Vector search features will not work without Ollama."
    fi
else
    echo "⚠️  Ollama not installed. Install from https://ollama.ai"
    echo "   The app will run but LLM features won't work."
fi

# Backend setup - using root-level venv
echo ""
echo "[2/4] Setting up backend..."

# Create venv at project root if it doesn't exist
if [ ! -d "$ROOT/.venv" ]; then
    echo "Creating Python virtual environment at project root..."
    python3 -m venv "$ROOT/.venv"
fi

# Activate venv
source "$ROOT/.venv/bin/activate"

# Install dependencies from backend/requirements.txt
echo "Installing backend dependencies..."
pip install -q --upgrade pip
pip install -q -r "$ROOT/backend/requirements.txt"

# Start backend in background
echo "Starting backend server on http://localhost:8000..."
cd "$ROOT/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!

cd "$ROOT"

# Frontend setup
echo ""
echo "[3/4] Setting up frontend..."
cd "$ROOT/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --silent
fi

# Start frontend
echo "Starting frontend server on http://localhost:5173..."
export VITE_API_BASE_URL="http://localhost:8000"
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!

cd "$ROOT"

# Wait a moment for servers to start
sleep 2

# Display status
echo ""
echo "[4/4] Services started!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Backend:  http://localhost:8000"
echo "✓ API Docs: http://localhost:8000/docs"
echo "✓ Frontend: http://localhost:5173"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✓ Services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for interrupt
wait

