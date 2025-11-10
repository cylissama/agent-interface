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
        orm_mode = True


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
        orm_mode = True


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    created_at: Optional[datetime] = None
    messages: list[Message] = []

    class Config:
        orm_mode = True
