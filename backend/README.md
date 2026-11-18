# AI Opti Matrix Backend & Notebook Automation System

Full-stack backend providing FastAPI endpoints and background Playwright automation that integrates the PHP frontend with the **Gemini Notebook**.

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
                                           │  Prompt Template Engine │
                                           │  Prompt Template.txt    │
                                           │  replaces {user_question}│
                                           └────────────┬────────────┘
                                                        │
                                                        ▼
                                           ┌─────────────────────────┐
                                           │  Playwright Automation  │
                                           │  (Headless Background)  │
                                           │  backend/browser_profile│
                                           └────────────┬────────────┘
                                                        │
                                                        ▼
                                           ┌─────────────────────────┐
                                           │  Google Gemini Notebook │
                                           │  (Persistent Session)   │
                                           └─────────────────────────┘
```

---

## 📁 Key Files & Modules

| File | Purpose |
|------|---------|
| `backend/app/services/notebook_automation.py` | Headless Playwright service managing the background Gemini Notebook connection, prompt submission, and response extraction. |
| `backend/app/services/chat_service.py` | Orchestrates prompt generation, dispatches to Notebook automation, manages session histories, and provides fallback. |
| `backend/app/main.py` | FastAPI application exposing `/ask`, `/history/{session_id}`, `/notebook/execute`, and `/notebook/status`. |
| `backend/Prompt Template.txt` | Prompt instructions & rules with the `{user_question}` dynamic placeholder. |
| `backend/browser_profile/` | Persistent authenticated Chromium profile (stores Google login cookies & tokens). |
| `frontend/index.php` | Modern chat UI connected to `http://localhost:8000/ask`. |

---

## 🚀 Running the Project

### 1. Start the Backend:
```powershell
.\backend\myenv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --app-dir backend
```
Backend will be available at:
- **API URL**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Start the PHP Frontend:
```powershell
php -S localhost:3000 -t frontend
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Testing the Workflow

1. In the chat interface at [http://localhost:3000](http://localhost:3000), enter any question (e.g., *"What services do you provide?"* or *"What is your contact number?"*).
2. The frontend sends the question to `http://localhost:8000/ask`.
3. The backend reads `Prompt Template.txt`, replaces `{user_question}`, and submits the complete prompt to your **Gemini Notebook** in the background.
4. Once Gemini finishes generating, the backend extracts the response and sends it back to the frontend.
5. The frontend displays the formatted response in the chat bubble!
