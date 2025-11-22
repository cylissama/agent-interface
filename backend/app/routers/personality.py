from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import minstrel_service

router = APIRouter()


class PersonalityRequest(BaseModel):
    character: str
    conversation_id: int


@router.post("/generate")
async def generate_personality(
    request: PersonalityRequest,
    db: Session = Depends(get_db),
):
    """Generate a personality prompt using GROQ Minstrel API based on character name."""
    from ..models import Conversation
    from ..config import get_settings
    
    # Check if GROQ API key is configured
    settings = get_settings()
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=400, 
            detail="GROQ_API_KEY not configured. Please set it in your .env file in the project root."
        )
    
    if not request.character or not request.character.strip():
        raise HTTPException(status_code=400, detail="Character name cannot be empty")
    
    # Get or create conversation
    conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    if not conversation:
        conversation = Conversation(
            id=request.conversation_id,
            title=f"Conversation {request.conversation_id}",
            created_at=datetime.now(),
        )
        db.add(conversation)
        db.commit()
    
    # Generate personality prompt using GROQ Minstrel API
    try:
        personality_prompt = await minstrel_service.generate_personality_prompt(request.character.strip())

        # Save personality prompt to conversation
        conversation.personality_prompt = personality_prompt
        db.commit()
        db.refresh(conversation)
        
        return {
            "success": True,
            "character": request.character,
            "personality_prompt": personality_prompt,
        }
    except ValueError as e:
        # Configuration errors (e.g., missing API key)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = str(e)
        print(f"Error generating personality: {error_details}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate personality: {error_details}")

