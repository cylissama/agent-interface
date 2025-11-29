from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services import llm_service

router = APIRouter()


@router.get("/conversation/{conversation_id}", response_model=schemas.Conversation)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    from ..models import Conversation
    
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return schemas.Conversation(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[],
    )


@router.post("/completion", response_model=schemas.Message)
async def create_completion(
    request: Request,
    message: schemas.MessageCreate,
    document_ids: Optional[List[int]] = Query(None),
    urls: Optional[List[str]] = Query(None),
    use_rag: bool = Query(True, description="Auto-search vector store for relevant context"),
    db: Session = Depends(get_db),
):
    """Generate an LLM response with optional document/URL context and automatic RAG search."""
    from ..models import Message, Conversation, Document
    from pathlib import Path
    
    # Get URLs from raw query params (most reliable)
    raw_urls = request.query_params.getlist('urls')
    if raw_urls:
        urls = raw_urls
    elif urls and isinstance(urls, str):
        urls = [urls]
    else:
        urls = urls or []
    
    # Get system info to determine recommended model
    from ..services import system_service
    system_info = await system_service.get_system_info()
    recommended_model = system_info["recommended_model"]
    
    # Create conversation if it doesn't exist
    conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    if not conversation:
        conversation = Conversation(
            id=message.conversation_id,
            title=f"Conversation {message.conversation_id}",
            created_at=datetime.now(),
            model_name=recommended_model,
        )
        db.add(conversation)
        db.commit()
    elif not conversation.model_name:
        conversation.model_name = recommended_model
        db.commit()
    
    # Get conversation history
    conversation_messages = (
        db.query(Message)
        .filter(Message.conversation_id == message.conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    
    history = [{"role": msg.role, "content": msg.content} for msg in conversation_messages]
    history.append({"role": message.role, "content": message.content})
    
    # Build context using ContextManager
    from ..services.context_manager import ContextManager
    from ..utils.web_scraper import extract_text_from_url
    
    context_manager = ContextManager(max_tokens=4000)
    
    # Add documents to context
    if document_ids:
        documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
        for doc in documents:
            doc_path = Path(doc.path)
            if doc_path.exists():
                from ..utils.file_handlers import extract_text
                text = extract_text(doc_path)
                if text and len(text.strip()) > 0:
                    context_manager.add_source(content=text, source_type="file", source_name=doc.name)
    
    # Add URLs to context
    if urls:
        for url in urls:
            text = extract_text_from_url(url, timeout=30.0)
            if text and len(text.strip()) > 50:
                context_manager.add_source(content=text, source_type="url", source_name=url)
    
    # Auto-search vector store for relevant context (RAG)
    if use_rag:
        try:
            from ..services.vector_store import get_vector_store
            vector_store = get_vector_store()
            
            # Only search if vector store has content
            stats = vector_store.get_stats()
            if stats["total_chunks"] > 0:
                search_results = vector_store.search(query=message.content, n_results=3)
                for result in search_results:
                    # Only include results with decent similarity
                    if result["similarity"] > 0.3:
                        source_name = result["metadata"].get("source_name", "vector-search")
                        context_manager.add_source(
                            content=result["content"],
                            source_type="vector-search",
                            source_name=f"{source_name} (relevance: {result['similarity']:.0%})"
                        )
        except Exception:
            pass  # Vector store not available, continue without RAG
    
    # Format context for LLM
    context_text, _ = context_manager.format_context()
    
    # Use conversation's model or fall back to recommended
    model_name = conversation.model_name or recommended_model
    
    # Generate response
    context_parts = [context_text] if context_text else None
    assistant_response = await llm_service.generate_response(
        prompt=message.content,
        context=context_parts,
        conversation_history=history[:-1],
        model_name=model_name,
    )
    
    # Save messages to database
    user_message = Message(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        created_at=datetime.now(),
    )
    db.add(user_message)
    
    assistant_message = Message(
        conversation_id=message.conversation_id,
        role="assistant",
        content=assistant_response,
        created_at=datetime.now(),
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return schemas.Message(
        id=assistant_message.id,
        conversation_id=assistant_message.conversation_id,
        role=assistant_message.role,
        content=assistant_message.content,
        created_at=assistant_message.created_at,
    )
