from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db

router = APIRouter()


@router.get("/", response_model=list[schemas.Document])
def list_documents(db: Session = Depends(get_db)):
    """List uploaded documents."""
    # Placeholder implementation
    return []


@router.post("/", response_model=schemas.Document)
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    """Upload a document and return metadata."""
    # Placeholder implementation
    return schemas.Document(id=0, name=file.filename, path="/tmp", created_at=None)
