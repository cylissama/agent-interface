"""
Vector store API endpoints for semantic search and document indexing.
"""
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Document
from ..services.vector_store import get_vector_store
from ..utils.file_handlers import extract_text
from ..utils.web_scraper import extract_text_from_url

router = APIRouter()


# Request/Response Models
class IndexDocumentRequest(BaseModel):
    """Request to index a document by ID."""
    document_id: int
    chunk_size: int = 500


class IndexUrlRequest(BaseModel):
    """Request to index content from a URL."""
    url: str
    chunk_size: int = 500


class IndexTextRequest(BaseModel):
    """Request to index raw text."""
    text: str
    source_name: str
    chunk_size: int = 500


class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str
    n_results: int = 5
    source_type: Optional[str] = None
    document_id: Optional[int] = None


class SearchResult(BaseModel):
    """A single search result."""
    content: str
    source_name: str
    similarity: float
    chunk_index: int
    total_chunks: int


class SearchResponse(BaseModel):
    """Search response with results."""
    query: str
    results: list[SearchResult]
    total_results: int


# Endpoints
@router.post("/index/document")
async def index_document(
    request: IndexDocumentRequest,
    db: Session = Depends(get_db),
):
    """
    Index a document from the database into the vector store.
    Extracts text and creates searchable embeddings.
    """
    # Get document from database
    doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Extract text from file
    doc_path = Path(doc.path)
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")
    
    text = extract_text(doc_path)
    if not text or len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Could not extract text from document")
    
    # Index in vector store
    vector_store = get_vector_store()
    result = vector_store.add_document(
        text=text,
        source_name=doc.name,
        source_type="document",
        document_id=doc.id,
        chunk_size=request.chunk_size,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Indexing failed"))
    
    return result


@router.post("/index/url")
async def index_url(request: IndexUrlRequest):
    """
    Index content from a URL into the vector store.
    Scrapes the URL and creates searchable embeddings.
    """
    # Extract text from URL
    text = extract_text_from_url(request.url, timeout=30.0)
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not extract content from URL")
    
    # Index in vector store
    vector_store = get_vector_store()
    result = vector_store.add_document(
        text=text,
        source_name=request.url,
        source_type="url",
        chunk_size=request.chunk_size,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Indexing failed"))
    
    return result


@router.post("/index/text")
async def index_text(request: IndexTextRequest):
    """
    Index raw text into the vector store.
    Useful for indexing content that's already extracted.
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text too short to index")
    
    vector_store = get_vector_store()
    result = vector_store.add_document(
        text=request.text,
        source_name=request.source_name,
        source_type="text",
        chunk_size=request.chunk_size,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Indexing failed"))
    
    return result


@router.post("/index/all")
async def index_all_documents(db: Session = Depends(get_db)):
    """
    Index all documents from the database into the vector store.
    """
    documents = db.query(Document).all()
    
    if not documents:
        return {"message": "No documents to index", "indexed": 0, "failed": 0}
    
    vector_store = get_vector_store()
    indexed = 0
    failed = 0
    results = []
    
    for doc in documents:
        doc_path = Path(doc.path)
        if not doc_path.exists():
            results.append({"document_id": doc.id, "name": doc.name, "success": False, "error": "File not found"})
            failed += 1
            continue
        
        text = extract_text(doc_path)
        if not text or len(text.strip()) < 10:
            results.append({"document_id": doc.id, "name": doc.name, "success": False, "error": "No text extracted"})
            failed += 1
            continue
        
        result = vector_store.add_document(
            text=text,
            source_name=doc.name,
            source_type="document",
            document_id=doc.id,
        )
        
        results.append({
            "document_id": doc.id,
            "name": doc.name,
            "success": result["success"],
            "chunks_indexed": result.get("chunks_indexed", 0),
        })
        
        if result["success"]:
            indexed += 1
        else:
            failed += 1
    
    return {
        "message": f"Indexed {indexed} documents, {failed} failed",
        "indexed": indexed,
        "failed": failed,
        "details": results,
    }


@router.post("/search", response_model=SearchResponse)
async def search_vectors(request: SearchRequest):
    """
    Perform semantic search across indexed documents.
    Returns the most relevant chunks based on meaning, not just keywords.
    """
    vector_store = get_vector_store()
    
    results = vector_store.search(
        query=request.query,
        n_results=request.n_results,
        source_type=request.source_type,
        document_id=request.document_id,
    )
    
    formatted_results = []
    for r in results:
        meta = r.get("metadata", {})
        formatted_results.append(SearchResult(
            content=r["content"],
            source_name=meta.get("source_name", "Unknown"),
            similarity=r["similarity"],
            chunk_index=meta.get("chunk_index", 0),
            total_chunks=meta.get("total_chunks", 1),
        ))
    
    return SearchResponse(
        query=request.query,
        results=formatted_results,
        total_results=len(formatted_results),
    )


@router.get("/search")
async def search_vectors_get(
    query: str = Query(..., description="Search query"),
    n_results: int = Query(5, description="Number of results"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
):
    """
    GET endpoint for semantic search (convenient for testing).
    """
    request = SearchRequest(query=query, n_results=n_results, source_type=source_type)
    return await search_vectors(request)


@router.get("/stats")
async def get_vector_stats():
    """
    Get statistics about the vector store.
    """
    vector_store = get_vector_store()
    return vector_store.get_stats()


@router.delete("/document/{document_id}")
async def delete_document_vectors(document_id: int):
    """
    Delete all vectors for a specific document.
    """
    vector_store = get_vector_store()
    result = vector_store.delete_by_document_id(document_id)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Delete failed"))
    
    return result


@router.delete("/source/{source_name:path}")
async def delete_source_vectors(source_name: str):
    """
    Delete all vectors for a specific source (by name/URL).
    """
    vector_store = get_vector_store()
    result = vector_store.delete_by_source(source_name)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Delete failed"))
    
    return result


@router.delete("/clear")
async def clear_vector_store():
    """
    Clear all vectors from the store. Use with caution!
    """
    vector_store = get_vector_store()
    result = vector_store.clear()
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Clear failed"))
    
    return result

