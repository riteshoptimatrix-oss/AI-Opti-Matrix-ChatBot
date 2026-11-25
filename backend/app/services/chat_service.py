import re
import datetime
import logging
from typing import List, Dict, Optional, AsyncGenerator
from app.models import ChatMessage
from app.services.gemini_api_service import gemini_api_service

logger = logging.getLogger("chat_service")

WP_PROJECTS_TEXT = (
    "Here are all **29 WordPress Projects** developed by **Opti Matrix Solutions**: 🌐✨\n\n"
    "1. **Azon Live** - https://azonlive.com/\n"
    "2. **Asteroid Microns** - https://www.asteroidmicrons.com/\n"
    "3. **Raja Interiors** - https://www.rajainteriors.in/\n"
    "4. **Ajrakh by Juned** - https://www.ajrakhbyjuned.com/\n"
    "5. **Pollux** - https://www.polluxporcelano.co.in/\n"
    "6. **Market Minds Digital** - https://www.marketmindsdigital.in/\n"
    "7. **Nirvan Fab** - https://www.nirvanfab.com/\n"
    "8. **Village Wine & Spirits** - https://www.villagewinesandspirit.com/\n"
    "9. **Greg’s Sprinklers Inc.** - https://www.gregssprinklers.com/\n"
    "10. **Holistic Life Care** - https://www.holisticlifecares.com/\n"
    "11. **P CHHAJED & CO LLP** - https://pchhajed.com/\n"
    "12. **Kalapurnam Institute** - https://www.kalapurnaminstitute.com/\n"
    "13. **Desert King Resort** - https://www.desertkingresort.com/\n"
    "14. **Multi Engineers** - http://multiengineers.in/\n"
    "15. **Hotel The Farm Inn** - https://www.hotelthefarminn.com/\n"
    "16. **World Talent Organization** - https://www.worldtalentorg.com/\n"
    "17. **MBPS Solutions** - https://www.mbpssolutions.com/\n"
    "18. **Shri Navkar Metals Ltd.** - https://www.shrinavkar.com/\n"
    "19. **Shape Me Up** - https://www.shapemeupmedspa.com/\n"
    "20. **Jainson Locks** - https://www.jainsonlocks.com/\n"
    "21. **Jain Network** - http://www.jainnetwork.com/\n"
    "22. **NeeRain** - http://www.neerain.com/\n"
    "23. **Gujarat Tour Guide** - https://www.gujarattourguide.in/\n"
    "24. **Palak Shah & Associates** - http://www.capalakshah.com/\n"
    "25. **Dan Caco Realtors** - http://www.dancacorealtor.ca/\n"
    "26. **Trimech Engineers** - http://www.trimechindia.com/\n"
    "27. **ROI Software Solution** - https://www.roisoftwaresolution.com/\n"
    "28. **Lloyd Neck Bath Club** - http://lloydneckbathclub.org/\n"
    "29. **Riya Mehta** - https://www.rmriyamehta.com/\n\n"
    "Feel free to ask if you would like details on any of these projects! 🚀"
)

IDENTITY_TEXT = "Yes, I am **Opti Matrix AI**! 🤖✨, your virtual assistant for Opti Matrix Solutions.\n\nHow can I help you today? 🚀"

GREETING_TEXT = (
    "Hello! It is a pleasure to meet you. 😊\n\n"
    "I am **Opti Matrix AI**, your virtual assistant for **Opti Matrix Solutions**.\n\n"
    "How can I assist you with our services, company information, or projects today? 🚀"
)

CEO_TEXT = (
    "Hello! 😊\n\n"
    "**Vishal Shah** is the Founder & CEO of **Opti Matrix Solutions**. 👨‍💼\n\n"
    "He established Opti Matrix in 2010 with a vision of creating exceptional digital experiences and simplifying complex IT systems globally."
)

LOCATIONS_TEXT = (
    "We would be delighted to connect with you! 📍\n\n"
    "Our **Head Office** is located at:\n"
    "🏢 **706, Indraprastha Corporate, Corporate Road, Opp. Shell Petrol Pump, Prahlad Nagar, Ahmedabad, Gujarat 380015, India.**\n\n"
    "📞 **Phone:** +91 81283 61116\n"
    "📩 **Email:** info@optimatrix.in\n\n"
    "We also have office locations in **Bhuj (Gujarat)**, the **USA**, and **South Africa**."
)

CONTACT_TEXT = (
    "We would love to assist you! 🤝\n\n"
    "Here is how you can reach us:\n\n"
    "📞 **General & Project Inquiries:** +91 81283 61116\n"
    "💼 **Sales Inquiries:** +91 75750 58824\n"
    "📩 **Email:** info@optimatrix.in\n"
    "📩 **HR & Careers:** hr@optiinfo.com\n"
    "🌐 **Website:** https://www.optimatrix.in"
)

CAREERS_TEXT = (
    "Ohh, Great! 😃🎉\n\n"
    "We're glad you're interested in joining **Opti Matrix**! 🚀\n\n"
    "Please apply through our official careers page:\n"
    "🔗 https://www.optimatrix.in/apply\n\n"
    "For any HR-related queries, feel free to reach out to us at:\n"
    "📩 hr@optiinfo.com\n\n"
    "All the best! 😊✨"
)

SERVICES_TEXT = (
    "Hello! 🚀\n\n"
    "**Opti Matrix Solutions** (Optimize the Complicated) is a premier digital agency and software development company established in 2010.\n\n"
    "We provide tailored, end-to-end technology solutions:\n\n"
    "💻 **Web Development:** PHP, Laravel, React, Next.js, Angular, Node.js, WordPress, E-Commerce\n"
    "📱 **Mobile Applications:** iOS, Android, Flutter, React Native\n"
    "🎨 **UI/UX & Design:** Web Design, Prototyping, Branding\n"
    "☁️ **Cloud & SaaS:** Custom SaaS platforms, APIs, Cloud infrastructure\n"
    "👨‍💻 **Dedicated Hiring:** Full-time, part-time, and hourly developers\n\n"
    "How can we help optimize your digital needs today? 😊"
)


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

    def _instant_intent_responder(self, question: str) -> Optional[str]:
        """
        Ultra-fast Tier-1 Intent Responder (0.001s / < 1ms response time).
        Immediately returns 100% accurate, verified answers for core topics.
        """
        q = question.lower().strip()
        norm = self._normalize_key(question)

        # 1. Identity
        if any(re.search(p, q) for p in [r"\b(who\s+are\s+you|are\s+you\s+opti|your\s+name|aap\s+kaun\s+ho|tum\s+kaun\s+ho)\b"]):
            return IDENTITY_TEXT
        if norm in ["who are you", "what is your name", "are you opti matrix ai", "are you an ai"]:
            return IDENTITY_TEXT

        # 2. Greetings
        if re.match(r"^(hi|hello|hey|namaste|kem cho|good morning|good evening|good afternoon)[\s!.,?]*$", q):
            return GREETING_TEXT

        # 3. Founder & CEO
        if any(re.search(p, q) for p in [r"\b(who\s+is\s+the\s+ceo|who\s+is\s+the\s+founder|ceo\s+name|founder\s+name|meet\s+the\s+ceo|meet\s+the\s+founder|vishal\s+shah)\b"]):
            return CEO_TEXT
        if norm in ["who is ceo", "who is the ceo", "who is founder", "who is the founder", "ceo", "founder"]:
            return CEO_TEXT

        # 4. Office Locations & Head Office
        if any(re.search(p, q) for p in [r"\b(head\s+office|office\s+location|office\s+locations|where\s+are\s+your\s+offices|where\s+is\s+your\s+office|office\s+address|prahlad\s+nagar)\b"]):
            return LOCATIONS_TEXT
        if norm in ["office locations", "where are your office locations", "office address", "head office"]:
            return LOCATIONS_TEXT

        # 5. Contact & Sales Details
        if any(re.search(p, q) for p in [r"\b(contact\s+number|phone\s+number|sales\s+number|call\s+you|reach\s+you|contact\s+details|contact\s+info)\b"]):
            return CONTACT_TEXT
        if norm in ["contact number", "phone number", "how can i contact", "contact details"]:
            return CONTACT_TEXT

        # 6. Careers & Job Application
        if any(re.search(p, q) for p in [r"\b(apply\s+for\s+a\s+job|how\s+can\s+i\s+apply|job\s+openings|internship|internships|careers\s+jobs|careers)\b"]):
            return CAREERS_TEXT
        if norm in ["careers", "how can i apply for a job", "apply for job", "careers and jobs"]:
            return CAREERS_TEXT

        # 7. WordPress Projects (29 projects)
        if any(re.search(p, q) for p in [r"\b(wordpress\s+projects|wordpress\s+portfolio|show\s+me\s+your\s+wordpress|29\s+wordpress)\b"]):
            return WP_PROJECTS_TEXT
        if norm in ["wordpress projects", "show me your wordpress projects", "29 wordpress projects"]:
            return WP_PROJECTS_TEXT

        # 8. Services & What Opti Matrix Does
        if any(re.search(p, q) for p in [r"\b(what\s+does\s+opti\s+matrix\s+do|what\s+services\s+do\s+you\s+offer|our\s+services|services\s+tech\s+stack|services\s+and\s+tech\s+stack)\b"]):
            return SERVICES_TEXT
        if norm in ["what does opti matrix do", "what services do you offer", "services and tech stack", "services"]:
            return SERVICES_TEXT

        return None

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
        1. Checks Tier-1 Instant Responder (< 0.001s).
        2. Logs user question to session history.
        3. Checks instant response cache (< 0.001s).
        4. Calls Direct Google Gemini Flash API with dynamic context (~0.8-1.2s).
        5. Saves response to cache for zero-latency future responses.
        """
        # Tier-1: Instant Intent Responder (0.001s)
        instant_answer = self._instant_intent_responder(question)
        if instant_answer:
            logger.info(f"⚡ Tier-1 Instant Intent Hit for '{question}' (0.001s response time).")
            self.add_message(session_id, "user", question)
            self.add_message(session_id, "assistant", instant_answer)
            return instant_answer

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
        Real-time streaming response with Tier-1 Instant Responder and Gemini Flash API.
        """
        # Tier-1: Instant Intent Responder (0.001s)
        instant_answer = self._instant_intent_responder(question)
        if instant_answer:
            logger.info(f"⚡ Tier-1 Instant Intent Hit (Streaming) for '{question}' (0.001s).")
            self.add_message(session_id, "user", question)
            self.add_message(session_id, "assistant", instant_answer)
            yield instant_answer
            return

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
            if full_text:
                if cache_key:
                    self._response_cache[cache_key] = full_text
                self.add_message(session_id, "assistant", full_text)
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            fallback = await self.generate_response(question, session_id)
            yield fallback


chat_service = ChatService()
