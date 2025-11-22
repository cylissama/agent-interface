# Agent Interface

A terminal-style chat interface powered by Ollama LLM.

## Setup

### Prerequisites

1. **Ollama** - Install from [ollama.ai](https://ollama.ai)
2. **Python 3.11+** with virtual environment
3. **Node.js** for frontend

### Quick Start

1. **Start Ollama** (if not already running):
   ```bash
   ollama serve
   ```

2. **Pull a model** (optional, defaults to llama3.2):
   ```bash
   ollama pull llama3.2
   ```

3. **Configure settings** (optional):
   Create a `.env` file in the project root:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_BASE_URL=https://api.groq.com
   GROQ_MODEL=mixtral-8x7b-32768
   ```
   
   To get a GROQ API key:
   - Go to [Groq Console](https://console.groq.com/)
   - Sign up or log in
   - Navigate to API Keys section
   - Create a new API key
   - Add it to your `.env` file

4. **Start the project:**
   
   **Windows (PowerShell):**
   ```powershell
   .\StartDev.ps1
   ```
   
   **Note:** If you get an execution policy error, run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\StartDev.ps1
   ```
   
   **Linux/Mac:**
   ```bash
   chmod +x StartDev.sh
   ./StartDev.sh
   ```

   This single command will:
   - Check prerequisites (Python, Node.js)
   - Create/activate Python virtual environment at project root (`.venv/`)
   - Install all dependencies (backend Python packages & frontend npm packages)
   - Start backend server on http://localhost:8000
   - Start frontend server on http://localhost:5173
   - Display all service URLs
   
   **Note:** The project uses a single Python virtual environment at the project root (`.venv/`) for all Python dependencies. The frontend uses npm/node_modules (not a Python environment).

5. **Open your browser:**
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs

Press `Ctrl+C` in the terminal to stop all services.

## Configuration

- **Ollama Base URL**: Defaults to `http://localhost:11434`
- **Ollama Model**: Defaults to `llama3.2`
- **GROQ API Key**: Required for personality generation via Minstrel API
- **GROQ Base URL**: Defaults to `https://api.groq.com`
- **GROQ Model**: Defaults to `mixtral-8x7b-32768` (adjust if using a specific Minstrel model)
- **Database**: SQLite database at `./agent.db`

Override these in a `.env` file or environment variables.

## Personality System

The personality system uses GROQ Minstrel API to generate detailed character personality prompts:

1. User enters a character name (e.g., "Trevor from GTA V")
2. The character name is sent to GROQ Minstrel API
3. Minstrel generates a detailed personality prompt with traits, speech patterns, and mannerisms
4. The generated personality prompt is saved to the conversation
5. All subsequent Ollama responses use this personality context until a new personality is selected
