import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models import (
    AskRequest,
    AskResponse,
    HistoryResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScreenshotRequest,
    ScreenshotResponse,
    PlaywrightStatusResponse,
    GeminiSessionStatusResponse,
)
from app.services.chat_service import chat_service
from app.services.playwright_service import playwright_service
from app.services.notebook_automation import notebook_automation
from gemini_session import GeminiSessionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("opti_matrix_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI AI Opti Matrix Backend starting up...")
    yield
    logger.info("FastAPI AI Opti Matrix Backend shutting down...")
    await notebook_automation.close()


app = FastAPI(
    title="AI Opti Matrix Backend API",
    description="FastAPI + Playwright backend for AI Opti Matrix Assistant and Gemini Notebook automation.",
    version="1.0.0",
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
        "version": "1.0.0",
        "docs_url": "/docs"
    }


# Chat Endpoints
@app.post("/ask", response_model=AskResponse, tags=["Chat"])
async def ask_question(payload: AskRequest):
    """
    Main chat endpoint used by the PHP frontend.
    Submits user question through Prompt Template.txt into the background Gemini Notebook,
    waits for generation to complete, and returns the formatted response.
    """
    session_id = payload.session_id or "default"
    try:
        answer = await chat_service.generate_response(payload.question, session_id)
        return AskResponse(answer=answer, session_id=session_id)
    except Exception as e:
        logger.error(f"Error handling /ask: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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


# Notebook Direct Automation Endpoints
@app.post("/notebook/execute", response_model=AskResponse, tags=["Notebook Automation"])
async def execute_notebook_prompt(payload: AskRequest):
    """
    Direct endpoint to execute a user prompt via the background Gemini Notebook.
    """
    try:
        answer = await notebook_automation.submit_question(payload.question)
        return AskResponse(answer=answer, session_id=payload.session_id or "direct")
    except Exception as e:
        logger.error(f"Error in /notebook/execute: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/notebook/status", tags=["Notebook Automation"])
async def get_notebook_status():
    """
    Returns the current status of the background Notebook automation service.
    """
    return {
        "notebook_url": settings.GEMINI_NOTEBOOK_URL,
        "profile_dir": str(settings.BROWSER_PROFILE_DIR),
        "template_path": str(settings.PROMPT_TEMPLATE_PATH),
        "template_exists": settings.PROMPT_TEMPLATE_PATH.exists(),
        "is_ready": notebook_automation._page is not None and not notebook_automation._page.is_closed()
    }


# Playwright Web Scraping Endpoints
@app.post("/scrape", response_model=ScrapeResponse, tags=["Playwright"])
async def scrape_webpage(payload: ScrapeRequest):
    """
    Uses Playwright headless Chromium to scrape dynamic webpage content.
    """
    try:
        result = await playwright_service.scrape_page(
            url=payload.url,
            wait_selector=payload.wait_selector,
            wait_timeout_ms=payload.wait_timeout_ms,
            extract_text_only=payload.extract_text_only
        )
        return ScrapeResponse(**result)
    except Exception as e:
        logger.error(f"Error in /scrape: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/screenshot", response_model=ScreenshotResponse, tags=["Playwright"])
async def take_screenshot(payload: ScreenshotRequest):
    """
    Captures a full or viewport screenshot of a webpage using Playwright.
    """
    try:
        result = await playwright_service.take_screenshot(
            url=payload.url,
            full_page=payload.full_page,
            wait_ms=payload.wait_ms
        )
        return ScreenshotResponse(**result)
    except Exception as e:
        logger.error(f"Error in /screenshot: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/playwright/status", response_model=PlaywrightStatusResponse, tags=["Playwright"])
async def check_playwright_status():
    """
    Verifies that the Playwright browser is properly installed and launchable.
    """
    status_info = await playwright_service.check_status()
    return PlaywrightStatusResponse(
        status=status_info.get("status", "unknown"),
        engine=status_info.get("engine", "Playwright Chromium"),
        chromium_available=status_info.get("chromium_available", False)
    )


# Gemini Session Management Endpoints
gemini_mgr = GeminiSessionManager()

@app.get("/gemini/status", response_model=GeminiSessionStatusResponse, tags=["Gemini Session"])
async def gemini_status():
    """
    Checks the status of the persistent Google session & lock.
    """
    state = gemini_mgr.get_state()
    return GeminiSessionStatusResponse(
        status=state.get("status", "uninitialized"),
        is_locked=gemini_mgr.is_locked(),
        profile_dir=str(gemini_mgr.profile_dir),
        notebook_url=gemini_mgr.notebook_url,
        details=state
    )


@app.post("/gemini/save", tags=["Gemini Session"])
async def gemini_save():
    """
    Triggers save for an active manual Google login session.
    """
    gemini_mgr.trigger_save()
    return {"success": True, "message": "Save trigger sent to active login session."}


@app.post("/gemini/stop", tags=["Gemini Session"])
async def gemini_stop():
    """
    Triggers stop for an active browser session.
    """
    gemini_mgr.trigger_stop()
    return {"success": True, "message": "Stop trigger sent."}
