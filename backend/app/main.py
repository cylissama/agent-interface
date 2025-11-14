from fastapi import FastAPI

from .routers import chat, documents, batch

app = FastAPI(title="Agent Interface API")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(batch.router, prefix="/batch", tags=["batch"])
