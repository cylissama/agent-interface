from datetime import datetime
import csv  # <--- Added import
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

# Define the CSV log file path
CSV_LOG_FILE = UPLOAD_DIR / "upload_log.csv"

def log_to_csv(entry_type: str, name: str, reference: str):
    """
    Appends an upload entry to the CSV file.
    Creates the file with headers if it doesn't exist.
    """
    file_exists = CSV_LOG_FILE.exists()
    
    with open(CSV_LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(['Timestamp', 'Type', 'Name', 'Location'])
            
        # Write the entry
        writer.writerow([
            datetime.now().isoformat(),
            entry_type,
            name,
            reference
        ])

@router.get("/", response_model=list[schemas.Document])
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    return db.query(Document).all()


@router.post("/upload", response_model=list[schemas.Document])
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more documents, extract text, and log to CSV."""
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
        db.flush() # Flush to get the ID if needed immediately, though not strictly necessary here
        uploaded_docs.append(doc)

        # --- LOG TO CSV ---
        # We store the absolute path to the file
        log_to_csv(
            entry_type="File", 
            name=file.filename, 
            reference=str(file_path.absolute())
        )
    
    db.commit()
    
    for doc in uploaded_docs:
        db.refresh(doc)
    
    return uploaded_docs


@router.post("/urls", response_model=dict)
async def process_urls(urls: List[str]):
    """Process one or more URLs, extract content, and log to CSV."""
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
                
                # --- LOG TO CSV ---
                log_to_csv(
                    entry_type="URL", 
                    name=url,  # Using URL as name since web pages might not have a clean title here
                    reference=url
                )
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
    
    # Note: We usually do NOT remove lines from a historical log (CSV) 
    # when deleting the actual file, as the log serves as a history record.
    
    return {"message": "Document deleted"}