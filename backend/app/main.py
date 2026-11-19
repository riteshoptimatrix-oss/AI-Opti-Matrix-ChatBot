import json
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models import (
    AskRequest,
    AskResponse,
    HistoryResponse,
)
from app.services.chat_service import chat_service
from app.services.gemini_api_service import gemini_api_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("opti_matrix_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI AI Opti Matrix Backend starting up...")
    logger.info("⚡ Engine Active: AI Assistant Engine.")
    yield
    logger.info("FastAPI AI Opti Matrix Backend shutting down...")
    await gemini_api_service.close()


app = FastAPI(
    title="AI Opti Matrix Backend API",
    description="FastAPI backend for AI Opti Matrix Assistant.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True if origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "app": "AI Opti Matrix Backend",
        "version": "2.0.0"
    }


# Chat Endpoints
@app.get("/ask", tags=["Chat"])
async def ask_question_get(
    question: Optional[str] = None,
    q: Optional[str] = None,
    session_id: Optional[str] = "default"
):
    """
    Handles GET requests to /ask so opening the URL directly in a browser
    returns 200 OK and allows quick testing via ?question= or ?q=.
    """
    query = question or q
    if query and query.strip():
        answer = await chat_service.generate_response(query.strip(), session_id)
        return AskResponse(answer=answer, session_id=session_id)
    return {
        "status": "online",
        "endpoint": "/ask",
        "description": "Send a POST request with JSON body {'question': 'your query'} or use ?question= in the browser."
    }


@app.post("/ask", response_model=AskResponse, tags=["Chat"])
async def ask_question(payload: AskRequest):
    """
    Main chat endpoint used by the PHP frontend.
    Processes user questions using Company Context and Prompt Template.
    """
    session_id = payload.session_id or "default"
    try:
        answer = await chat_service.generate_response(payload.question, session_id)
        return AskResponse(answer=answer, session_id=session_id)
    except Exception as e:
        logger.error(f"Error handling /ask: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/ask/stream", tags=["Chat"])
async def ask_question_stream(payload: AskRequest):
    """
    Real-time streaming chat endpoint:
    Streams newly generated tokens via Server-Sent Events (SSE).
    """
    session_id = payload.session_id or "default"

    async def sse_event_stream():
        try:
            async for chunk in chat_service.generate_response_stream(payload.question, session_id):
                payload_str = json.dumps({"chunk": chunk})
                yield f"data: {payload_str}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            err_json = json.dumps({"error": str(e)})
            yield f"data: {err_json}\n\n"

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")


@app.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_history(session_id: str):
    """
    Retrieves the conversation history for a given session.
    """
    history = chat_service.get_history(session_id)
    return HistoryResponse(session_id=session_id, chat_history=history)


@app.delete("/history/{session_id}", tags=["Chat"])
async def clear_history(session_id: str):
    """
    Clears the conversation history for a given session.
    """
    cleared = chat_service.clear_history(session_id)
    return {"session_id": session_id, "cleared": cleared}
