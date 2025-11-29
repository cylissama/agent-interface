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
   ```

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
- **Database**: SQLite database at `./agent.db`

Override these in a `.env` file or environment variables.

## Overview of All Features

# routers (contains batch, chat, documents, system)

- batch: process multiple prompts in a single request with shared document/URL context. Useful for bulk Q&A, running multiple questions against the same sources.

- chat (where the llm operates): combines message, conversation, added documents, and urls to generate the llm response

- documents: manages documents added in database

- system: gets system information to determine if user has gpu or not (if user only has cpu uses a lighter ollama model)

# services (context_manager, llm_service, system_service, vector_store)

- context_manager: adds all needed context to response. Fetches documents from database and adds urls/files to context.

- llm_service: includes the hardcoded context opener for every prompt, calls the ollama api

- system_service: detects the system gpu or cpu

- vector_store: under construction

# utils (file_handlers, web_scraper)

- file_handlers: extracts text from all filetypes using pdfplumber, then pyPDF if that doesnt work. Other libraries work for each file type

- web_scraper: starts with Jina Reader API, if that doesnt work then tries direct HTML scraping, if that doesnt work then uses trafilatura

# app (config, database, main)

- standard stuff

