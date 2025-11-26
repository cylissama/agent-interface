from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List

from .. import schemas
from ..database import get_db
from ..models import Document
from ..utils.file_handlers import save_upload, extract_text

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_model=list[schemas.Document])
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    return db.query(Document).all()


@router.post("/upload", response_model=list[schemas.Document])
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more documents and extract text."""
    uploaded_docs = []
    
    for file in files:
        # Validate file type
        allowed_extensions = {'.pdf', '.txt', '.doc', '.docx', '.md', '.rtf'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        file_path = save_upload(file, UPLOAD_DIR)
        
        # Save to database
        doc = Document(
            name=file.filename,
            path=str(file_path),
            created_at=datetime.now(),
        )
        db.add(doc)
        db.flush()
        uploaded_docs.append(doc)
    
    db.commit()
    
    for doc in uploaded_docs:
        db.refresh(doc)
    
    return uploaded_docs


@router.post("/urls", response_model=dict)
async def process_urls(urls: List[str]):
    """Process one or more URLs and extract content."""
    from ..utils.web_scraper import extract_text_from_url
    
    results = []
    
    for url in urls:
        try:
            text = extract_text_from_url(url, timeout=30.0)
            
            if text:
                word_count = len(text.split())
                results.append({
                    "url": url,
                    "content": text,
                    "success": True,
                    "content_length": len(text),
                    "word_count": word_count,
                    "estimated_tokens": word_count
                })
            else:
                results.append({
                    "url": url,
                    "content": None,
                    "success": False,
                    "error": "No content extracted from URL"
                })
        except Exception as e:
            results.append({
                "url": url,
                "content": None,
                "success": False,
                "error": str(e)
            })
    
    return {"results": results}


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Delete a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    file_path = Path(doc.path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted"}
