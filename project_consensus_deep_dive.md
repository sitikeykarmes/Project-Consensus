# Project Consensus: Deep Dive Architecture & Implementation Details

## 1. Executive Summary
**Project Consensus** is a first-of-its-kind multi-user, multi-AI collaborative workspace. It goes beyond simple chatbot interfaces by integrating multiple human users and a suite of specialized AI agents into a single, unified real-time chat environment. The system intelligently monitors human-to-human conversations and autonomously intervenes to provide synthesized, multi-modal AI reasoning only when needed.

## 2. Core Architecture

### Frontend (React & WebSockets)
- **Framework**: Built with React (Vite) and styled with custom CSS (`index.css`).
- **Real-time Engine**: Connects to the backend via native WebSockets (`ChatWindow.jsx`).
- **State Management**: Uses optimistic UI updates to instantly render user messages while waiting for backend confirmation. Handles complex AI states like `typing`, `consensus_stream` (streaming tokens), and final `consensus` payloads.
- **Dynamic UI**: Components like `MessageBubble.jsx` dynamically render historical messages vs. active streaming messages.

### Backend (FastAPI & Python)
- **Framework**: FastAPI running on Uvicorn. Provides REST APIs for auth/groups and a robust WebSocket endpoint (`/api/ws/{room_id}`) for real-time bidirectional communication.
- **Database**: SQLite (`whatsapp_aidb.db`) via SQLAlchemy. Stores users, groups, messages, and conversation summaries.
- **Connection Manager**: Broadcasts messages to all connected clients in a specific room and maintains live online status.

---

## 3. The AI Pipeline Lifecycle

When a user sends a message in a group chat, it triggers a sophisticated, multi-stage AI pipeline:

### Phase 1: Hybrid Memory Construction (`context_builder.py`)
To prevent infinite token context windows while preserving memory, the system uses a **Hybrid Context Memory**:
- **Recent Window**: The last 15 messages are fetched verbatim.
- **Compression**: Once older messages exceed a threshold (e.g., 10 messages outside the recent window), a background LLM process summarizes them.
- **Final Output**: The AI is fed a context block containing `[Summary of earlier conversation] + [Recent 15 verbatim messages]`.

### Phase 2: The Gatekeeper (`intent_classifier.py`)
The system acts as an "invisible eavesdropper." It does not process every message:
- **Regex Fast-Lane**: Bypasses LLM checks for obvious triggers (e.g., "@ai", "explain").
- **LLM Evaluation**: If a message requires deeper analysis, a fast LLM (`llama-3.3-70b-versatile`) evaluates if the message is a casual human-to-human interaction (returns `NO`) or requires AI intervention (returns `YES`).

### Phase 3: Intent Classification (`intent_classifier.py`)
Once invoked, the AI must decide *how* to think. It classifies the query into one of three distinct reasoning modes:
1. **Independent Mode (Comparison)**: Best for brainstorming and comparisons (e.g., "React vs Angular").
2. **Support Mode (Supplement)**: Best for deep, sequential explanations (e.g., "How does a blockchain work?").
3. **Opposition Mode (Debate)**: Best for fact-checking and controversial topics (e.g., "Is the moon landing fake?").

### Phase 4: Multi-Agent Execution (`app/agents/`)
Depending on the mode, a specialized team of LLMs goes to work:
- **Agent Arsenal**: 
  - Agent 1: `openai/gpt-oss-120b` (Generator / Lead)
  - Agent 2: `llama-3.1-8b-instant` (Critic / Supplementer)
  - Agent 3: `moonshotai/kimi-k2-instruct-0905` (Investigator)
  - Agent 4: `llama-3.3-70b-versatile` (Chief Judge)

**Mode Mechanics:**
- **Independent**: Three agents generate parallel, diverse perspectives.
- **Support**: Agent 1 outlines the core answer, Agent 2 adds nuance, Agent 3 finds missing details.
- **Opposition (The Courtroom)**: 
  - *Generator* makes a claim.
  - *Critic* attacks the logic.
  - *Investigator* fact-checks both.
  - *Chief Judge* issues a verdict.
  - This loops for up to 5 rounds until a final, verified truth is established.

### Phase 5: Master Synthesis Engine (`orchestrator.py`)
Once the agents finish their internal processes, their raw logs are passed to the **Master Synthesis Engine** (Agent 5: `meta-llama/llama-4-scout-17b-16e-instruct`).
- **Role**: It acts as the final authority. It does *not* merely summarize the agents; it independently verifies their claims, drops hallucinated facts, and combines the best insights into a single, cohesive, highly-refined response.
- **Streaming**: The Master Synthesis Engine streams its output token-by-token back to the frontend via WebSockets for a low-latency user experience.

---

## 4. The Evaluation Suite (`app/Evaluation/`)

To ensure the AI is performing optimally, the backend features a dual-layer evaluation framework:

### Layer 1: Deterministic Evaluator (`Evaluator.py`)
Uses purely mathematical and statistical metrics (TF-IDF, ROUGE) to calculate:
- **Faithfulness**: Is the synthesis grounded in the agents' responses?
- **Relevance**: Cosine similarity and query term coverage.
- **Conciseness**: Compression ratio to prevent bloated answers.
- **Coherence**: Sentence length variance and Type-Token Ratio.

### Layer 2: LLM Judges (e.g., `opposition_evaluator.py`)
Stringent JSON-only LLM judges calculate specialized proprietary metrics dynamically:
- **PDS (Perspective Diversity Score)**
- **ICS (Iterative Coherence Score)**
- **EDR (Error Detection Rate)**
- **HallucinationRate**: Severe penalties applied if the Master Synthesizer hallucinates facts not present in the agent logs or its own training data.

---

## 5. Summary of Innovation
Project Consensus successfully solves several major problems in modern LLM applications:
1. **Context Bloat**: Solved via Hybrid Memory.
2. **API Cost / Rate Limits**: Solved via the Gatekeeper mechanism.
3. **Hallucinations**: Solved via adversarial debate (Opposition Mode) and a strict Master Synthesis Engine.
4. **UX Friction**: Solved via real-time WebSockets and streaming responses in a familiar group-chat interface.
