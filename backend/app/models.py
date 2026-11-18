from typing import List, Optional
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(..., description="User query or message")
    session_id: Optional[str] = Field("default", description="Session identifier for maintaining conversation context")

class AskResponse(BaseModel):
    answer: str = Field(..., description="AI response text or formatted card data")
    session_id: str = Field(..., description="Session identifier")

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text or card data")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")

class HistoryResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="List of previous messages in session")

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="Webpage URL to scrape")
    wait_selector: Optional[str] = Field(None, description="CSS selector to wait for before extracting")
    wait_timeout_ms: int = Field(30000, description="Timeout in milliseconds")
    extract_text_only: bool = Field(True, description="Whether to extract clean text or full HTML")

class ScrapeResponse(BaseModel):
    success: bool
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None

class ScreenshotRequest(BaseModel):
    url: str = Field(..., description="Webpage URL to screenshot")
    full_page: bool = Field(True, description="Whether to capture full scrollable page")
    wait_ms: int = Field(1500, description="Delay before capture in milliseconds")

class ScreenshotResponse(BaseModel):
    success: bool
    url: str
    image_base64: Optional[str] = None
    error: Optional[str] = None

class PlaywrightStatusResponse(BaseModel):
    status: str
    engine: str
    chromium_available: bool

class GeminiSessionStatusResponse(BaseModel):
    status: str
    is_locked: bool
    profile_dir: str
    notebook_url: str
    details: Optional[dict] = None
