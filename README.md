# Consensus — Multi-Agent AI Group Chat Platform

A real-time group chat platform where multiple AI agents collaborate, debate, and synthesize answers using different reasoning modes. Built with FastAPI, React, WebSockets, and Groq LLMs.

---

## What It Does

Users chat in groups. Every message is processed by 3 AI agents working in parallel or sequentially depending on the query type. A fourth synthesis agent (Qwen3-32b) reads all agent responses and produces a single, coherent final answer. Every response is evaluated automatically using a hybrid deterministic + LLM judge scoring system.

```
User Message
     │
     ▼
Intent Classifier (llama-3.3-70b)
     │
     ├── independent  →  3 agents give parallel perspectives
     ├── support      →  3 agents build on each other sequentially
     └── opposition   →  agents debate, referee, repeat until verdict
                               │
                               ▼
                     Synthesis Agent (Qwen3-32b)
                               │
                               ▼
                     Hybrid Evaluator (prints to terminal)
                               │
                               ▼
                        Final Answer → User
```

---

## Tech Stack

| Layer        | Technology                               |
| ------------ | ---------------------------------------- |
| Backend      | FastAPI, Python 3.11+                    |
| Frontend     | React, Tailwind CSS                      |
| Real-time    | WebSockets                               |
| Database     | SQLite (local) → PostgreSQL (production) |
| LLM Provider | Groq API                                 |
| Auth         | JWT (python-jose)                        |
| ORM          | SQLAlchemy                               |

---

## AI Agents

| Agent      | Model                                       | Role                             |
| ---------- | ------------------------------------------- | -------------------------------- |
| Agent 1    | `openai/gpt-oss-120b`                       | Generator / Lead                 |
| Agent 2    | `meta-llama/llama-4-scout-17b-16e-instruct` | Critic / Supplement              |
| Agent 3    | `moonshotai/kimi-k2-instruct-0905`          | Referee / Third perspective      |
| Agent 4    | `qwen/qwen3-32b`                            | Synthesizer + Context Summarizer |
| Classifier | `llama-3.3-70b-versatile`                   | Intent classification            |
| Judge      | `llama-3.3-70b-versatile`                   | Evaluation (LLM layer)           |

---

## Orchestration Modes

### Independent Mode

Three agents respond in parallel, each from a different angle. Best for comparisons, brainstorming, pros/cons, and multi-perspective questions.

### Support Mode

Agents respond sequentially — each builds on the previous. Agent 1 gives the main answer, Agent 2 adds nuance, Agent 3 adds final points others missed. Best for explanations, tutorials, and how-to questions.

### Opposition Mode (Debate)

Adversarial pipeline with up to 5 rounds:

1. Generator (Agent 1) gives initial answer
2. Critic (Agent 2) challenges or corrects it
3. Referee (Agent 3) evaluates both and gives a verdict
4. If `VERDICT REACHED` → stops early, else Generator updates and repeats

Best for fact-checking, controversial claims, and verification questions.

---

## Project Structure

```
project-consensus/
├── backend/
│   ├── server.py                        # Uvicorn entry point
│   └── app/
│       ├── main.py                      # FastAPI app, WebSocket handler
│       ├── agents/
│       │   ├── orchestrator.py          # Main pipeline coordinator
│       │   ├── independent_mode.py
│       │   ├── support_mode.py
│       │   └── opposition_mode.py
│       ├── auth/
│       │   ├── auth_routes.py           # Login / register endpoints
│       │   └── ws_auth.py               # WebSocket JWT validation
│       ├── groups/
│       │   └── group_routes.py          # Group CRUD
│       ├── chat/
│       │   └── chat_routes.py
│       ├── db/
│       │   ├── database.py              # SQLAlchemy engine + session
│       │   ├── models.py                # ORM models
│       │   ├── init_db.py               # Table creation on startup
│       │   └── message_service.py       # Save / load messages
│       ├── models/
│       │   └── schemas.py               # Pydantic schemas
│       └── utils/
│           ├── LLM_agent_client.py      # Groq client wrapper (all 4 agents)
│           ├── intent_classifier.py     # Routes query to correct mode
│           ├── context_builder.py       # Hybrid memory (summary + recent)
│           └── evaluator.py             # Hybrid evaluation (det + LLM judge)
│
└── frontend/
    └── src/
        └── components/
            ├── ChatWindow.jsx           # WebSocket connection, message state
            ├── MessageBubble.jsx        # User / Consensus / System messages
            ├── MessageRenderer.jsx      # Markdown + syntax highlighting
            ├── ChatInput.jsx
            ├── ChatHeader.jsx
            └── TypingIndicator.jsx
```

---

## Database Schema

```
users                groups              group_members
─────────────────    ──────────────────  ──────────────────────
id (PK)              id (PK)             id (PK)
email                name                group_id (FK → groups)
hashed_password      agents (JSON)       user_id  (FK → users)
created_at           created_by          joined_at
                     created_at

messages                                conversation_summaries
──────────────────────────────────────  ──────────────────────────────────
id (PK)                                 id (PK)
group_id (FK → groups)                  group_id (FK → groups, unique)
sender_id                               summary_text
sender_name                             messages_covered
sender_type  (user / consensus)         last_message_id
content                                 updated_at
extra_data   (JSON: mode, agent_responses)
timestamp
```

---

## Hybrid Context Memory

Every AI response uses a two-layer context window instead of a simple last-N-messages approach.

```
All messages in DB
├── [Older messages]  →  compressed into ~200 word summary  →  stored in conversation_summaries
└── [Last 15 msgs]    →  verbatim, fetched fresh every time

AI receives: [Summary] + [15 recent messages]
```

**Trigger:** Summary regenerates every time `(total_messages - messages_covered) - 15 >= 10`. The summary is built by Agent 4 (Qwen) and always extends the previous summary rather than replacing it from scratch.

**Configured in** `app/utils/context_builder.py`:

```python
RECENT_WINDOW   = 15   # verbatim messages always included
SUMMARY_TRIGGER = 10   # regenerate after this many new summarizable messages
```

---

## Hybrid Evaluator

After every synthesis, a scorecard is printed to the terminal. Zero impact on response sent to user.

### Layer 1 — Deterministic (no LLM)

| Metric         | Method                                                             |
| -------------- | ------------------------------------------------------------------ |
| Faithfulness   | ROUGE-1/2/L recall — synthesis content grounded in agent responses |
| Relevance      | TF-IDF cosine similarity + query term coverage                     |
| Conciseness    | Compression ratio: synthesis tokens / agent tokens (ideal 10–50%)  |
| Coherence      | Avg sentence length + Type-Token Ratio + bigram repetition         |
| Agent Coverage | Token overlap between synthesis and each individual agent          |

### Layer 2 — LLM Judge (semantic)

Uses `llama-3.3-70b-versatile` — a different model from the synthesizer to avoid self-grading bias. The judge is **anchored** to the deterministic scores before it evaluates, forcing it to justify any significant deviation.

### Fusion

```
final_score = w_det × deterministic_score + w_llm × llm_score_normalized

Faithfulness:    0.70 det + 0.30 llm   (ROUGE is more objective here)
Relevance:       0.55 det + 0.45 llm
Conciseness:     0.45 det + 0.55 llm   (LLM understands query type better)
Coherence:       0.50 det + 0.50 llm
Agent Coverage:  0.60 det + 0.40 llm
```

**Conflict detection:** if deterministic and LLM scores differ by ≥ 2 points (on 1–5 scale), a `⚑ CONFLICT` flag is printed with both scores and the LLM's reasoning.

### Verdict Rules

- ✅ **PASS** — all fused scores ≥ 0.40 and faithfulness ≥ 0.50
- ⚠️ **WARN** — faithfulness 0.30–0.50, or relevance < 0.35, or 2+ conflicts
- ❌ **FAIL** — faithfulness < 0.30 (strong hallucination signal)

### Synthesis vs Agents

A second section compares the synthesis against each individual agent on Relevance, Coherence, and Vocabulary Richness — showing delta scores and a `BETTER ↑ / SIMILAR = / WORSE ↓` verdict per agent.

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install rouge-score scikit-learn
```

Create `.env` in `backend/`:

```env
GROQ_API_KEY_1=your_groq_api_key
GROQ_API_KEY=your_groq_api_key
JWT_SECRET_KEY=your_secret_key
```

Start the server:

```bash
uvicorn server:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm install react-markdown react-syntax-highlighter remark-gfm
npm run dev
```

---

## API Reference

### Auth

| Method | Endpoint         | Description    |
| ------ | ---------------- | -------------- |
| POST   | `/auth/register` | Create account |
| POST   | `/auth/login`    | Get JWT token  |

### Groups

| Method | Endpoint                   | Description        |
| ------ | -------------------------- | ------------------ |
| GET    | `/api/groups`              | List user's groups |
| POST   | `/api/groups`              | Create group       |
| GET    | `/api/groups/{id}/members` | List members       |
| POST   | `/api/groups/{id}/members` | Add member         |

### Chat

| Protocol  | Endpoint                      | Description    |
| --------- | ----------------------------- | -------------- |
| WebSocket | `/api/ws/{room_id}?token=JWT` | Real-time chat |

### WebSocket Message Format

**Sending:**

```json
{ "message": "explain how RAG works" }
```

**Receiving (consensus):**

```json
{
  "type": "consensus",
  "sender_name": "AI Consensus",
  "content": "...",
  "mode_used": "support",
  "agent_responses": [
    { "agent_name": "Agent 1", "content": "..." },
    { "agent_name": "Agent 2", "content": "..." },
    { "agent_name": "Agent 3", "content": "..." }
  ],
  "timestamp": "2026-03-14T10:30:00"
}
```

---

## One-time Scripts

### Backfill summaries for existing groups

Run once if you have groups with many messages but no summary yet:

```python
# run from backend/ directory
# python backfill_summaries.py

import sys
sys.path.insert(0, ".")
from app.db.database import SessionLocal
from app.utils.context_builder import build_hybrid_context

GROUP_IDS = [
    "paste-your-group-ids-here",
]

for group_id in GROUP_IDS:
    print(f"Backfilling {group_id[:8]}...")
    db = SessionLocal()
    try:
        build_hybrid_context(db, group_id)
    finally:
        db.close()
```

---

## Production Notes

**Switch from SQLite to PostgreSQL** (one line change in `.env`):

```env
DATABASE_URL=postgresql://user:password@host/dbname
```

SQLite works fine for local development but will throw `database is locked` errors under concurrent WebSocket connections in production. Supabase and Neon both have free PostgreSQL tiers that work out of the box with this setup.

**Recommended:** Run with multiple Uvicorn workers in production:

```bash
uvicorn server:app --workers 4 --host 0.0.0.0 --port 8001
```

---

## Environment Variables

| Variable         | Required | Description                                |
| ---------------- | -------- | ------------------------------------------ |
| `GROQ_API_KEY_1` | ✅       | Used by all agents and the evaluator judge |
| `GROQ_API_KEY`   | ✅       | Used by the intent classifier              |
| `JWT_SECRET_KEY` | ✅       | Signs auth tokens                          |
| `DATABASE_URL`   | ❌       | Defaults to `sqlite:///./whatsapp_aidb.db` |
