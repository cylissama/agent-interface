from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentBase(BaseModel):
    name: str


class DocumentCreate(DocumentBase):
    path: str


class Document(DocumentBase):
    id: int
    path: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    conversation_id: int


class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    created_at: Optional[datetime] = None
    messages: list[Message] = []

    class Config:
        from_attributes = True


class ContextMetadata(BaseModel):
    """Metadata about context sources used in a conversation."""
    total_sources: int
    total_chunks: int
    estimated_tokens: int
    truncated: bool = False
    included_sources: Optional[int] = None
    included_chunks: Optional[int] = None


# Batch Processing Schemas
class BatchPrompt(BaseModel):
    """A single prompt in a batch request."""
    prompt: str
    id: Optional[str] = None  # Optional client-provided ID for tracking


class BatchRequest(BaseModel):
    """Request for batch processing multiple prompts."""
    prompts: list[BatchPrompt]
    document_ids: Optional[list[int]] = None  # Shared context documents
    urls: Optional[list[str]] = None  # Shared context URLs


class BatchResult(BaseModel):
    """Result for a single prompt in batch processing."""
    id: Optional[str] = None  # Echo back client ID if provided
    prompt: str
    response: str
    success: bool = True
    error: Optional[str] = None


class BatchResponse(BaseModel):
    """Response containing all batch results."""
    results: list[BatchResult]
    total: int
    successful: int
    failed: int
    context_metadata: Optional[ContextMetadata] = None