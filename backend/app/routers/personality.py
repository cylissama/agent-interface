from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import gemini_service

router = APIRouter()


class PersonalityRequest(BaseModel):
    character: str
    conversation_id: int


@router.post("/generate")
async def generate_personality(
    request: PersonalityRequest,
    db: Session = Depends(get_db),
):
    """Generate a personality prompt using Gemini based on character name."""
    from ..models import Conversation
    
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
    
    # Generate personality prompt using Gemini
    try:
        personality_prompt = await gemini_service.generate_personality_prompt(request.character)
        
        # Generate character image description
        character_image = await gemini_service.generate_character_image(request.character)
        
        # Save personality prompt and image to conversation
        conversation.personality_prompt = personality_prompt
        conversation.character_image_url = character_image  # Store description for now
        db.commit()
        db.refresh(conversation)
        
        return {
            "success": True,
            "character": request.character,
            "personality_prompt": personality_prompt,
            "character_image": character_image,  # Return image description/URL
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

