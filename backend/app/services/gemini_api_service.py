"""
Gemini Direct Flash API Service (Ultra-Fast 1-2s Response Engine).

Features:
- Direct HTTP REST API via official Google Gemini Flash models.
- Turnaround time: ~2.0 to 2.5 seconds flat.
- In-memory cached loading of Prompt Template.txt and Company's Context.txt.
- Persistent httpx.AsyncClient connection pooling.
- Streaming and non-streaming support.
- Automatic model fallback (gemini-3.1-flash-lite -> gemini-3.5-flash-lite -> gemini-flash-latest).
"""

import os
import re
import json
import logging
import httpx
from typing import Optional, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger("gemini_api_service")

MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]


class GeminiAPIService:
    def __init__(self):
        self.template_path = settings.PROMPT_TEMPLATE_PATH
        self.context_path = settings.COMPANY_CONTEXT_PATH

        self._cached_template: Optional[str] = None
        self._cached_context: Optional[str] = None
        self._template_mtime: float = 0.0
        self._context_mtime: float = 0.0
        self._client: Optional[httpx.AsyncClient] = None
        self._key_index: int = 0

    @property
    def api_keys(self) -> list[str]:
        """Returns list of active API keys configured in settings/env."""
        raw = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
        if raw:
            return [k.strip() for k in raw.split(",") if k.strip()]
        return settings.GEMINI_API_KEYS

    @property
    def api_key(self) -> str:
        keys = self.api_keys
        return keys[0] if keys else ""

    def get_rotated_keys(self) -> list[str]:
        """
        Returns keys in Round-Robin order.
        Distributes requests evenly across accounts and provides instant failover.
        """
        keys = self.api_keys
        if not keys:
            return []
        n = len(keys)
        start = self._key_index % n
        self._key_index = (self._key_index + 1) % n
        return [keys[(start + i) % n] for i in range(n)]

    def _load_data(self):
        """Loads and caches Prompt Template.txt and Company's Context.txt in memory (reloads on file change)."""
        tmpl_mtime = self.template_path.stat().st_mtime if self.template_path.exists() else 0.0
        if self._cached_template is None or tmpl_mtime != self._template_mtime:
            if self.template_path.exists():
                self._cached_template = self.template_path.read_text(encoding="utf-8")
            else:
                self._cached_template = "USER QUESTION:\n{user_question}"
            self._template_mtime = tmpl_mtime

        ctx_mtime = self.context_path.stat().st_mtime if self.context_path.exists() else 0.0
        if self._cached_context is None or ctx_mtime != self._context_mtime:
            if self.context_path.exists():
                self._cached_context = self.context_path.read_text(encoding="utf-8")
            else:
                self._cached_context = ""
            self._context_mtime = ctx_mtime

    def build_prompt(self, user_question: str, conversation_history: str = "") -> str:
        """Constructs prompt using the template, conversation history, and company context."""
        self._load_data()
        prompt = self._cached_template

        hist_text = conversation_history.strip() if conversation_history else "No previous messages (This is the start of the chat)."
        if "{conversation_history}" in prompt:
            prompt = prompt.replace("{conversation_history}", hist_text)
        elif "USER QUESTION:" in prompt:
            prompt = prompt.replace("USER QUESTION:", f"CURRENT SESSION CONVERSATION HISTORY:\n{hist_text}\n\nUSER QUESTION:")

        if "{user_question}" in prompt:
            prompt = prompt.replace("{user_question}", user_question.strip())
        else:
            prompt = f"{prompt}\n\nUSER QUESTION:\n{user_question.strip()}"

        if self._cached_context:
            prompt = re.sub(
                r"COMPANY INFORMATION\s*:-\s*Company's Context\.txt file\s*",
                f"COMPANY INFORMATION :-\n{self._cached_context}\n",
                prompt,
                flags=re.IGNORECASE
            )
            if self._cached_context not in prompt and "COMPANY INFORMATION :-" in prompt:
                prompt = prompt.replace(
                    "COMPANY INFORMATION :-",
                    f"COMPANY INFORMATION :-\n{self._cached_context}"
                )
        return prompt

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._client

    async def generate_response(self, user_question: str, conversation_history: str = "") -> Optional[str]:
        """
        Sends prompt to Google's official Gemini Flash API.
        Returns generated answer in 2-3 seconds.
        """
        rotated_keys = self.get_rotated_keys()
        if not rotated_keys:
            return None

        prompt = self.build_prompt(user_question, conversation_history)
        client = await self.get_client()

        payload = {
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "You are Opti Matrix AI, the official intelligent AI assistant for Opti Matrix Solutions.\n"
                        "CRITICAL OPERATIONAL RULES:\n"
                        "1. YOUR IDENTITY: Your name is strictly **Opti Matrix AI**. If asked who you are, what your name is, or 'are you Opti Matrix AI?', always confirm clearly and enthusiastically: 'Yes, I am **Opti Matrix AI**! 🤖✨, your virtual assistant for Opti Matrix Solutions!'\n"
                        "2. CONVERSATION MEMORY: Refer directly to the CURRENT SESSION CONVERSATION HISTORY to accurately answer questions about previous messages, chat numbers, or earlier statements (e.g., 'what is my 3rd chat?', 'what was my first question?'). Never claim conversation memory is missing from company data!\n"
                        "3. FACTUAL ACCURACY & COMPLETENESS: Base company answers strictly on the provided company data. Never invent facts, emails, phones, or URLs. Never leave sentences or lists incomplete.\n"
                        "4. STRICT ENGLISH: Always reply in clean, professional English, regardless of the input language.\n"
                        "5. SPECIFIC TECHNOLOGY PROJECTS: When asked about projects of a specific technology (such as WordPress, PHP, Webflow), state the exact total count from the company data and list ALL matching projects with their name and URL.\n"
                        "6. STRUCTURE & POLISH: Structure answers neatly with clean spacing, bold highlights for key names/technologies, and clear bullet points. Keep answers crisp, complete, and easy to scan."
                    )
                }]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 3000
            }
        }

        # Try API keys in rotation with automatic failover
        for active_key in rotated_keys:
            for model in MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={active_key}"
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text:
                                    return text
                    elif res.status_code in (429, 403):
                        logger.warning(f"Key ending with ...{active_key[-6:]} returned {res.status_code}. Switching to next key...")
                        break
                    logger.warning(f"Model {model} returned {res.status_code}: {res.text[:100]}")
                except Exception as e:
                    logger.warning(f"Error querying {model} with key ...{active_key[-6:]}: {e}")

        return None

    async def generate_response_stream(self, user_question: str, conversation_history: str = "") -> AsyncGenerator[str, None]:
        """
        Streams generated response chunks via Server-Sent Events from Gemini Flash API.
        """
        rotated_keys = self.get_rotated_keys()
        if not rotated_keys:
            return

        prompt = self.build_prompt(user_question, conversation_history)
        client = await self.get_client()

        payload = {
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "You are Opti Matrix AI, the official intelligent AI assistant for Opti Matrix Solutions.\n"
                        "CRITICAL OPERATIONAL RULES:\n"
                        "1. YOUR IDENTITY: Your name is strictly **Opti Matrix AI**. If asked who you are, what your name is, or 'are you Opti Matrix AI?', always confirm clearly and enthusiastically: 'Yes, I am **Opti Matrix AI**! 🤖✨, your virtual assistant for Opti Matrix Solutions!'\n"
                        "2. CONVERSATION MEMORY: Refer directly to the CURRENT SESSION CONVERSATION HISTORY to accurately answer questions about previous messages, chat numbers, or earlier statements (e.g., 'what is my 3rd chat?', 'what was my first question?'). Never claim conversation memory is missing from company data!\n"
                        "3. FACTUAL ACCURACY & COMPLETENESS: Base company answers strictly on the provided company data. Never invent facts, emails, phones, or URLs. Never leave sentences or lists incomplete.\n"
                        "4. STRICT ENGLISH: Always reply in clean, professional English, regardless of the input language.\n"
                        "5. SPECIFIC TECHNOLOGY PROJECTS: When asked about projects of a specific technology (such as WordPress, PHP, Webflow), state the exact total count from the company data and list ALL matching projects with their name and URL.\n"
                        "6. STRUCTURE & POLISH: Structure answers neatly with clean spacing, bold highlights for key names/technologies, and clear bullet points. Keep answers crisp, complete, and easy to scan."
                    )
                }]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 3000
            }
        }

        for active_key in rotated_keys:
            for model in MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={active_key}"
                try:
                    async with client.stream("POST", url, json=payload) as response:
                        if response.status_code in (429, 403):
                            logger.warning(f"Streaming key ending in ...{active_key[-6:]} returned {response.status_code}. Trying next key...")
                            break
                        if response.status_code != 200:
                            continue
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if line.startswith("data: "):
                                raw_data = line[6:].strip()
                                if not raw_data:
                                    continue
                                try:
                                    chunk_json = json.loads(raw_data)
                                    candidates = chunk_json.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for part in parts:
                                            text = part.get("text", "")
                                            if text:
                                                yield text
                                except Exception:
                                    pass
                        return
                except Exception as e:
                    logger.warning(f"Streaming error on {model}: {e}")

        # Fallback to non-streaming if stream connection fails
        static_res = await self.generate_response(user_question)
        if static_res:
            yield static_res

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


gemini_api_service = GeminiAPIService()
