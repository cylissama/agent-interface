# 🖥️ Agent Interface

A retro terminal-style chat interface powered by **Ollama LLM** with RAG (Retrieval-Augmented Generation) capabilities. Upload documents, add URLs, and have intelligent conversations with context-aware AI.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Local LLM Chat** | Powered by Ollama - runs completely offline on your machine |
| 📄 **Document Upload** | Support for PDF, DOCX, TXT, MD, RTF, CSV files |
| 🌐 **URL Context** | Add website URLs for the AI to reference |
| 🔍 **Semantic Search (RAG)** | ChromaDB vector store with automatic document chunking |
| ⚡ **Batch Processing** | Process multiple prompts against the same sources |
| 📊 **Analytics Dashboard** | View indexed sources and vector store statistics |
| 🎨 **Retro Terminal UI** | Classic green-on-black terminal aesthetic |
| 🚀 **Auto GPU Detection** | Automatically selects optimal model for your hardware |

---

## 🚀 Quick Start

### Prerequisites

- [Ollama](https://ollama.ai) - Local LLM runtime
- Python 3.11+
- Node.js 18+

### One-Command Setup

**Windows (PowerShell):**
```powershell
.\StartDev.ps1
```

**Linux/Mac:**
```bash
chmod +x StartDev.sh && ./StartDev.sh
```

This will:
- ✅ Check prerequisites
- ✅ Pull required Ollama models (`llama3.2`, `nomic-embed-text`)
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Start backend (http://localhost:8000)
- ✅ Start frontend (http://localhost:5173)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│                   Terminal-style Chat Interface                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   /chat         │   /vectors      │   /batch                    │
│   Completions   │   RAG Search    │   Bulk Processing           │
└─────────────────┴─────────────────┴─────────────────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│     Ollama      │ │    ChromaDB     │ │      SQLite             │
│   LLM + Embed   │ │  Vector Store   │ │   Conversations         │
└─────────────────┘ └─────────────────┘ └─────────────────────────┘
```

---

## 📚 How It Works

### RAG Pipeline (Retrieval-Augmented Generation)

1. **Index** - Documents/URLs are chunked and embedded using `nomic-embed-text`
2. **Store** - Embeddings saved to ChromaDB vector database
3. **Search** - User query is embedded and matched against stored chunks
4. **Augment** - Top-k relevant chunks added to LLM context
5. **Generate** - LLM responds using retrieved context

```
User: "What is backpropagation?"
         │
         ▼
┌─────────────────────────────────────┐
│ 1. Embed query → [0.12, -0.34, ...] │
│ 2. Search ChromaDB → Top 3 chunks   │
│ 3. Filter → similarity > 30%        │
│ 4. Build context with snippets      │
│ 5. LLM generates answer             │
└─────────────────────────────────────┘
         │
         ▼
"Backpropagation is the algorithm used 
 to train neural networks by adjusting 
 weights based on the error gradient..."
```

### Auto-Indexing

When you attach documents or URLs in chat, they're **automatically indexed** to ChromaDB for future semantic search. No manual indexing required!

---

## 🔌 API Reference

### Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/completion` | POST | Send message with optional document/URL context |
| `/chat/conversation/{id}` | GET | Retrieve conversation history |

### Documents
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/upload` | POST | Upload files (PDF, DOCX, TXT, MD, RTF, CSV) |
| `/documents/` | GET | List all uploaded documents |
| `/documents/{id}` | DELETE | Remove a document |

### Vectors (RAG)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vectors/index/document` | POST | Index a document by ID |
| `/vectors/index/url` | POST | Index content from URL |
| `/vectors/index/text` | POST | Index raw text |
| `/vectors/search` | POST | Semantic search across indexed content |
| `/vectors/stats` | GET | Get vector store statistics |

### Batch Processing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/batch/completions` | POST | Process multiple prompts with shared context |
| `/batch/urls` | POST | Extract content from multiple URLs |

### System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/system/info` | GET | Get GPU status and recommended model |

📖 **Full API docs available at:** http://localhost:8000/docs

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Embedding Model (for RAG)
EMBEDDING_MODEL=nomic-embed-text

# Database
DATABASE_URL=sqlite:///./agent.db
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React, Vite |
| **Backend** | FastAPI, Python 3.11+ |
| **LLM** | Ollama (llama3.2) |
| **Embeddings** | nomic-embed-text |
| **Vector Store** | ChromaDB |
| **Database** | SQLite |
| **Document Parsing** | pdfplumber, python-docx, trafilatura |
| **Web Scraping** | Jina Reader API, BeautifulSoup |

---

## 📁 Project Structure

```
LLMInterface/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   │   ├── chat.py       # Chat completions
│   │   │   ├── documents.py  # File uploads
│   │   │   ├── vectors.py    # RAG/search
│   │   │   ├── batch.py      # Bulk processing
│   │   │   └── system.py     # System info
│   │   ├── services/         # Business logic
│   │   │   ├── llm_service.py
│   │   │   ├── vector_store.py
│   │   │   └── context_manager.py
│   │   └── utils/            # Helpers
│   │       ├── file_handlers.py
│   │       └── web_scraper.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   └── VisualizationModal.jsx
│   │   └── App.jsx
│   └── package.json
├── StartDev.ps1              # Windows startup script
├── StartDev.sh               # Linux/Mac startup script
└── README.md
```

---

## 🎯 Usage Examples

### Basic Chat
Simply type your message and press Enter. The AI will respond using the default model.

### Chat with Document Context
1. Click the 📎 attach button
2. Select PDF, DOCX, or other supported files
3. Ask questions about the document content

### Chat with URL Context
1. Enter a URL in the "Website URL Context" box
2. Click "Add URL"
3. Ask questions about the webpage content

### Batch Processing (Developer Console)
```javascript
fetch('http://localhost:8000/batch/completions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    prompts: [
      {prompt: "Summarize this", id: "q1"},
      {prompt: "List key points", id: "q2"}
    ],
    urls: ["https://example.com/article"]
  })
}).then(r => r.json()).then(console.log)
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ using Ollama, FastAPI, and React**

[Report Bug](../../issues) · [Request Feature](../../issues)

</div>
