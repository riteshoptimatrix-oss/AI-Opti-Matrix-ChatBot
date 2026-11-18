import json
import re
import datetime
import logging
from typing import List, Dict, Optional
from app.models import ChatMessage
from app.core.config import settings
from app.services.notebook_automation import notebook_automation

logger = logging.getLogger("chat_service")


class ChatService:
    def __init__(self):
        # In-memory session store: session_id -> list of ChatMessage
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def get_history(self, session_id: str) -> List[ChatMessage]:
        return self.sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        msg = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        self.sessions[session_id].append(msg)
        return msg

    def clear_history(self, session_id: str) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id] = []
            return True
        return False

    async def generate_response(self, question: str, session_id: str) -> str:
        """
        Main response generation pipeline:
        1. Logs user question to session history.
        2. Dispatches question through Prompt Template.txt into the background Gemini Notebook.
        3. Captures and returns the Notebook's response.
        4. In case of browser/page disconnect, automatically attempts one clean retry.
        """
        self.add_message(session_id, "user", question)

        # Primary attempt
        try:
            logger.info(f"Submitting question to background Gemini Notebook for session {session_id}...")
            notebook_response = await notebook_automation.submit_question(question)
            if notebook_response and notebook_response.strip():
                self.add_message(session_id, "assistant", notebook_response)
                return notebook_response
        except Exception as first_err:
            logger.warning(f"First attempt failed ({first_err}). Closing context and retrying once...")
            await notebook_automation.close()

        # Retry attempt after clean restart
        try:
            logger.info("Retrying prompt submission on fresh notebook page...")
            notebook_response = await notebook_automation.submit_question(question)
            if notebook_response and notebook_response.strip():
                self.add_message(session_id, "assistant", notebook_response)
                return notebook_response
        except Exception as retry_err:
            logger.error(f"Notebook automation retry failed: {retry_err}")
            error_msg = f"⚠️ Gemini Notebook Error: {retry_err}\n\nPlease ensure no visible Chrome window is locking the profile (close open_notebook.bat if running)."
            self.add_message(session_id, "assistant", error_msg)
            return error_msg


chat_service = ChatService()
