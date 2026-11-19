# AI Opti Matrix Backend (FastAPI + Google Gemini Flash API)

High-performance backend integrating the PHP frontend with **Google Gemini Flash API** for ultra-fast, context-grounded AI responses (2–3 seconds).

---

## 🏗️ Architecture & Workflow

```text
┌─────────────────┐       POST /ask        ┌─────────────────────────┐
│                 │ ─────────────────────> │  FastAPI Backend        │
│  PHP Frontend   │                        │  (app.main:app)         │
│  (index.php)    │ <───────────────────── │                         │
└─────────────────┘      { "answer" }      └────────────┬────────────┘
                                                        │
                                                        ▼
                                           ┌─────────────────────────┐
                                           │  In-Memory Context      │
                                           │  - Prompt Template.txt  │
                                           │  - Company's Context.txt│
                                           │  - LRU Instant Cache    │
                                           └────────────┬────────────┘
                                                        │
                                                        ▼
                                           ┌─────────────────────────┐
                                           │ Google Gemini Flash API │
                                           │ (gemini-3.1-flash-lite) │
                                           │ Turnaround: 2-3 seconds │
                                           └─────────────────────────┘
```

---

## 📁 Key Files & Modules

| File | Purpose |
|------|---------|
| `backend/app/main.py` | Clean FastAPI application exposing `/ask`, `/ask/stream`, `/history/{session_id}`. |
| `backend/app/services/gemini_api_service.py` | Direct async REST client for official Google Gemini Flash API with context injection. |
| `backend/app/services/chat_service.py` | Orchestrates query flow, LRU instant response caching (0.001s), and session history. |
| `backend/app/core/config.py` | Application settings and environment variables. |
| `backend/Company's Context.txt` | Complete company knowledge base (242KB: services, CEO, offices, policies, tech stack). |
| `backend/Prompt Template.txt` | Persona, response guidelines, rules, and link formatting. |
| `backend/.env` | Environment configuration (`GEMINI_API_KEY`, ports, CORS). |
| `frontend/index.php` | Modern glassmorphic chat interface connected to `http://localhost:8000/ask`. |

---

## 🚀 How to Run

1. **Start Backend**:
   - Double-click `start_backend.bat`
   - Or run: `.\backend\myenv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --app-dir backend`

2. **Start Frontend**:
   - Double-click `start_frontend.bat`
   - Or run: `php -S localhost:3000 -t frontend`

3. **Access**:
   - Open browser: `http://localhost:3000`
