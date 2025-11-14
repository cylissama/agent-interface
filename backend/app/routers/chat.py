from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
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
    """Get conversation details including character image."""
    from ..models import Conversation
    
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return schemas.Conversation(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[],
        character_image_url=conversation.character_image_url,
    )


@router.post("/completion", response_model=schemas.Message)
async def create_completion(
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
):
    """Generate an LLM response to user input."""
    from ..models import Message, Conversation
    
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
            model_name=recommended_model,  # Set recommended model on creation
        )
        db.add(conversation)
        db.commit()
    elif not conversation.model_name:
        # If conversation exists but no model set, update it
        conversation.model_name = recommended_model
        db.commit()
    
    # Get conversation history for context
    conversation_messages = (
        db.query(Message)
        .filter(Message.conversation_id == message.conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    
    # Build conversation history for the LLM
    history = []
    for msg in conversation_messages:
        history.append({"role": msg.role, "content": msg.content})
    
    # Add the current user message to history
    history.append({"role": message.role, "content": message.content})
    
    # Get personality prompt if set
    personality_prompt = conversation.personality_prompt if conversation else None
    
    # Use conversation's model or fall back to recommended
    model_name = conversation.model_name or recommended_model
    
    # Generate response using Ollama
    assistant_response = await llm_service.generate_response(
        prompt=message.content,
        conversation_history=history[:-1],  # Exclude current message from history
        personality_prompt=personality_prompt,
        model_name=model_name,
    )
    
    # Save user message to database
    user_message = Message(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        created_at=datetime.now(),
    )
    db.add(user_message)
    
    # Save assistant response to database
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
