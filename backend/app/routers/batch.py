from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Document
from ..services import llm_service, system_service
from ..services.context_manager import ContextManager
from ..utils.file_handlers import extract_text
from ..utils.web_scraper import extract_text_from_url

router = APIRouter()


@router.post("/completions", response_model=schemas.BatchResponse)
async def batch_completions(
    request: schemas.BatchRequest,
    db: Session = Depends(get_db),
):
    """
    Process multiple prompts in a batch with optional shared context.
    
    All prompts share the same document/URL context, making this efficient
    for asking multiple questions about the same source material.
    """
    results: list[schemas.BatchResult] = []
    successful = 0
    failed = 0
    
    # Get system info for model selection
    system_info = await system_service.get_system_info()
    model_name = system_info["recommended_model"]
    
    # Build shared context once (reused for all prompts)
    context_manager = ContextManager(max_tokens=4000)
    
    # Add documents to context
    if request.document_ids:
        documents = db.query(Document).filter(Document.id.in_(request.document_ids)).all()
        for doc in documents:
            doc_path = Path(doc.path)
            if doc_path.exists():
                text = extract_text(doc_path)
                if text and len(text.strip()) > 0:
                    context_manager.add_source(
                        content=text,
                        source_type="file",
                        source_name=doc.name
                    )
    
    # Add URLs to context
    if request.urls:
        for url in request.urls:
            text = extract_text_from_url(url, timeout=30.0)
            if text and len(text.strip()) > 50:
                context_manager.add_source(
                    content=text,
                    source_type="url",
                    source_name=url
                )
    
    # Format context once for all prompts
    context_text, context_meta = context_manager.format_context()
    context_parts = [context_text] if context_text else None
    
    # Process each prompt
    for batch_prompt in request.prompts:
        try:
            response = await llm_service.generate_response(
                prompt=batch_prompt.prompt,
                context=context_parts,
                conversation_history=None,  # Batch requests don't have history
                model_name=model_name,
            )
            
            results.append(schemas.BatchResult(
                id=batch_prompt.id,
                prompt=batch_prompt.prompt,
                response=response,
                success=True,
            ))
            successful += 1
            
        except Exception as e:
            results.append(schemas.BatchResult(
                id=batch_prompt.id,
                prompt=batch_prompt.prompt,
                response="",
                success=False,
                error=str(e),
            ))
            failed += 1
    
    # Build context metadata if we had context
    context_metadata = None
    if context_text:
        context_metadata = schemas.ContextMetadata(
            total_sources=context_meta.get("total_sources", 0),
            total_chunks=context_meta.get("total_chunks", 0),
            estimated_tokens=context_meta.get("estimated_tokens", 0),
            truncated=context_meta.get("truncated", False),
            included_sources=context_meta.get("included_sources"),
            included_chunks=context_meta.get("included_chunks"),
        )
    
    return schemas.BatchResponse(
        results=results,
        total=len(request.prompts),
        successful=successful,
        failed=failed,
        context_metadata=context_metadata,
    )


@router.post("/urls", response_model=dict)
async def batch_process_urls(
    urls: list[str],
):
    """
    Extract content from multiple URLs in batch.
    Returns extracted text and metadata for each URL.
    """
    results = []
    
    for url in urls:
        try:
            text = extract_text_from_url(url, timeout=30.0)
            
            if text and len(text.strip()) > 0:
                word_count = len(text.split())
                results.append({
                    "url": url,
                    "content": text,
                    "success": True,
                    "word_count": word_count,
                    "estimated_tokens": word_count,
                })
            else:
                results.append({
                    "url": url,
                    "content": None,
                    "success": False,
                    "error": "No content extracted",
                })
        except Exception as e:
            results.append({
                "url": url,
                "content": None,
                "success": False,
                "error": str(e),
            })
    
    successful = sum(1 for r in results if r["success"])
    
    return {
        "results": results,
        "total": len(urls),
        "successful": successful,
        "failed": len(urls) - successful,
    }
