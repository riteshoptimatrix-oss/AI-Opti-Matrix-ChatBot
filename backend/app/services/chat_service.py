import re
import datetime
import logging
from typing import List, Dict, Optional, AsyncGenerator
from app.models import ChatMessage
from app.services.gemini_api_service import gemini_api_service

logger = logging.getLogger("chat_service")


class ChatService:
    def __init__(self):
        # In-memory session store: session_id -> list of ChatMessage
        self.sessions: Dict[str, List[ChatMessage]] = {}
        # High-speed LRU response cache: normalized_question -> answer
        self._response_cache: Dict[str, str] = {}

    def _normalize_key(self, text: str) -> str:
        """Normalizes a question by stripping punctuation, extra spaces, and casing."""
        cleaned = re.sub(r"[^\w\s]", "", text.lower()).strip()
        return " ".join(cleaned.split())

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

    def format_history(self, session_id: str, current_question: str) -> str:
        """Formats prior conversation turns with clear numbering so the AI can recall previous chats."""
        history = self.get_history(session_id)
        if not history:
            return "No previous messages in this session. (Current message is the very first message)."

        lines = []
        user_turn_count = 0
        for msg in history[-14:]:  # last 14 messages for rich context
            if msg.role == "user":
                user_turn_count += 1
                lines.append(f"- User (User Message #{user_turn_count}): \"{msg.content}\"")
            else:
                lines.append(f"- Opti Matrix AI: \"{msg.content}\"")

        # Label the current incoming question
        current_num = user_turn_count + 1
        lines.append(f"- User (User Message #{current_num} - Current Question): \"{current_question}\"")
        return "\n".join(lines)

    def _is_context_dependent(self, text: str) -> bool:
        """Checks if question refers to ongoing conversation history or identity."""
        patterns = [
            r"\b(chat|chats|message|messages|previous|earlier|last|first|1st|2nd|3rd|4th|5th|before|again|repeat)\b",
            r"\b(my\s+question|my\s+chat|my\s+message|you\s+said|what\s+did\s+i|what\s+was\s+my|who\s+are\s+you|are\s+you|your\s+name)\b"
        ]
        lowered = text.lower()
        return any(re.search(p, lowered) for p in patterns)

    async def generate_response(self, question: str, session_id: str) -> str:
        """
        Main response generation pipeline:
        1. Formats conversation history for context awareness.
        2. Logs user question to session history.
        3. Checks instant response cache for non-conversational questions (< 0.001s).
        4. Calls Direct Google Gemini Flash API with history (~2.0s).
        5. Saves response to cache for zero-latency future responses.
        """
        history_context = self.format_history(session_id, question)
        self.add_message(session_id, "user", question)

        is_contextual = self._is_context_dependent(question)
        cache_key = self._normalize_key(question) if not is_contextual else None

        if cache_key and cache_key in self._response_cache:
            cached_answer = self._response_cache[cache_key]
            logger.info(f"Instant cache hit for '{question}' (0.001s response time).")
            self.add_message(session_id, "assistant", cached_answer)
            return cached_answer

        if not gemini_api_service.api_key:
            err_msg = "Error: GEMINI_API_KEY is not configured in backend/.env"
            logger.error(err_msg)
            self.add_message(session_id, "assistant", err_msg)
            return err_msg

        try:
            logger.info(f"Generating response via Gemini Flash API for session {session_id}...")
            api_response = await gemini_api_service.generate_response(question, conversation_history=history_context)
            if api_response and api_response.strip():
                if cache_key:
                    self._response_cache[cache_key] = api_response
                self.add_message(session_id, "assistant", api_response)
                return api_response
            else:
                err_msg = "Apologies, I could not generate a response at this moment. Please try again."
                self.add_message(session_id, "assistant", err_msg)
                return err_msg
        except Exception as e:
            logger.error(f"Error querying Gemini API: {e}")
            err_msg = f"Error generating response: {e}"
            self.add_message(session_id, "assistant", err_msg)
            return err_msg

    async def generate_response_stream(self, question: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        Real-time streaming response directly from Gemini Flash API with conversation history.
        """
        history_context = self.format_history(session_id, question)
        self.add_message(session_id, "user", question)

        is_contextual = self._is_context_dependent(question)
        cache_key = self._normalize_key(question) if not is_contextual else None

        # Check instant cache
        if cache_key and cache_key in self._response_cache:
            cached_answer = self._response_cache[cache_key]
            logger.info(f"Instant cache hit for '{question}' (streaming 0.001s).")
            self.add_message(session_id, "assistant", cached_answer)
            yield cached_answer
            return

        accumulated = []
        try:
            async for chunk in gemini_api_service.generate_response_stream(question, conversation_history=history_context):
                accumulated.append(chunk)
                yield chunk
            full_text = "".join(accumulated).strip()
            if full_text:
                if cache_key:
                    self._response_cache[cache_key] = full_text
                self.add_message(session_id, "assistant", full_text)
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            fallback = await self.generate_response(question, session_id)
            yield fallback


chat_service = ChatService()
