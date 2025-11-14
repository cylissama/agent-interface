from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import chat, documents, batch, personality, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup if needed


app = FastAPI(title="Agent Interface API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(batch.router, prefix="/batch", tags=["batch"])
app.include_router(personality.router, prefix="/personality", tags=["personality"])
app.include_router(system.router, prefix="/system", tags=["system"])
