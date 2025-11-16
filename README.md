# Agent Interface

A terminal-style chat interface powered by Ollama LLM.

## Setup

### Prerequisites

1. **Ollama** - Install from [ollama.ai](https://ollama.ai)
2. **Python 3.11+** with virtual environment
3. **Node.js** for frontend

### Backend Setup

1. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

3. Start Ollama (if not already running):
```bash
ollama serve
```

4. Pull a model (optional, defaults to llama3.2):
```bash
ollama pull llama3.2
# Or use another model like: ollama pull mistral
```

5. Configure settings (optional):
Create a `.env` file in the project root:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
GEMINI_API_KEY=your_gemini_api_key_here
```

   To get a Gemini API key:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file

6. Start the backend:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the dev server:
```bash
npm run dev
```

3. Open `http://localhost:5173` in your browser

### Quick Start (Both Services)

Use the provided script:
```bash
./start-dev.sh
```

This will start both backend and frontend servers.

## Configuration

- **Ollama Base URL**: Defaults to `http://localhost:11434`
- **Ollama Model**: Defaults to `llama3.2`
- **Database**: SQLite database at `./agent.db`

Override these in a `.env` file or environment variables.
