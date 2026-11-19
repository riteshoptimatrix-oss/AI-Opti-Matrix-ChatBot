from typing import List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., description="User query or message")
    session_id: Optional[str] = Field("default", description="Session identifier for maintaining conversation context")


class AskResponse(BaseModel):
    answer: str = Field(..., description="AI response text or formatted markdown")
    session_id: str = Field(..., description="Session identifier")


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text or card data")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class HistoryResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="List of previous messages in session")
