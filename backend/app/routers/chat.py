from fastapi import APIRouter

from .. import schemas

router = APIRouter()


@router.post("/completion", response_model=schemas.Message)
def create_completion(message: schemas.MessageCreate):
    """Generate an LLM response to user input."""
    # Placeholder implementation
    return schemas.Message(id=0, conversation_id=message.conversation_id, role="assistant", content="Response", created_at=None)
