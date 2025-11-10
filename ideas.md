# Project 2 LLM Powered Agent

Containerize it (Docker)

Stacks
- FastAPI w/ React + Viteand SQL

Example Projct Structure

project-root/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings/env vars
│   │   ├── database.py          # SQLite setup
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas (API contracts)
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py    # Document upload/management
│   │   │   ├── chat.py         # QA endpoints
│   │   │   └── batch.py        # Batch processing
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py    # Extract, chunk, embed
│   │   │   ├── llm_service.py         # LLM API calls
│   │   │   ├── vector_store.py        # ChromaDB operations
│   │   │   └── ocr_service.py         # OCR (advanced)
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_handlers.py       # PDF, DOCX extractors
│   │       └── web_scraper.py         # URL content fetch
│   │
│   ├── uploads/                 # Temporary file storage
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── DocumentList.jsx
│   │   │   └── AnswerDisplay.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js           # Axios API client
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md




