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
    character_image_url: Optional[str] = None

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