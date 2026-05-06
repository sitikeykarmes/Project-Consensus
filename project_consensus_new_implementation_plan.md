# Project Consensus — Production Implementation Plan
> Everything Anthropic would build, adapted for your stack.  
> Stack: FastAPI + Python + React + SQLite/SQLAlchemy + WebSockets

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Phase 1 — Four-Layer Memory System](#phase-1--four-layer-memory-system)
3. [Phase 2 — Token Budget Enforcement](#phase-2--token-budget-enforcement)
4. [Phase 3 — Unified Gatekeeper + Router](#phase-3--unified-gatekeeper--router)
5. [Phase 4 — Memory Assembly Service](#phase-4--memory-assembly-service)
6. [Phase 5 — Restructured Agent Modes](#phase-5--restructured-agent-modes)
7. [Phase 6 — Synthesis Engine as a Write Operation](#phase-6--synthesis-engine-as-a-write-operation)
8. [Phase 7 — Proactive AI Invocation](#phase-7--proactive-ai-invocation)
9. [Phase 8 — Member-Aware Context](#phase-8--member-aware-context)
10. [Phase 9 — Session Closing Report](#phase-9--session-closing-report)
11. [Phase 10 — Evaluation Suite Upgrade](#phase-10--evaluation-suite-upgrade)
12. [Implementation Order & Timeline](#implementation-order--timeline)
13. [Folder Structure After All Changes](#folder-structure-after-all-changes)

---

## Architecture Overview

### Current Flow (Project Consensus)
```
Message → context_builder → intent_classifier → gatekeeper → agents → synthesis → response
           (full history)    (full history)      (full hist)  (full)   (full)
```
Every phase receives full context. Context is unbounded. Token cost grows linearly.

### Target Flow (Production Grade)
```
Message → Unified Gatekeeper (last 3 msgs only, ~50ms)
               │
               ▼
        Memory Assembly Service (fixed 2000 token budget, assembled ONCE)
               │
               ▼
        Mode Execution (agents receive memory packet only)
               │
               ▼
        Synthesis Engine (receives agent outputs only, NOT context)
          │                    │
          ▼                    ▼
     Stream response    Async knowledge graph write (non-blocking)
```

Context is assembled **once**, has a **hard size limit**, and never grows beyond it regardless of conversation length or message size.

---

## Phase 1 — Four-Layer Memory System

### What You're Replacing
The current single `context_builder.py` that returns recent 15 messages + one summary.

### What You're Building
Four distinct memory layers per group, each with a different purpose, storage mechanism, and update cadence.

---

### Layer 1: Working Memory (In-Context)
**Purpose**: What is happening RIGHT NOW in this thread.  
**Storage**: Not persisted. Constructed fresh per invocation.  
**Size**: Hard cap of 500 tokens.  
**Contents**: Last 3–5 messages verbatim + current query.

**Implementation** — `app/memory/working_memory.py`:
```python
MAX_WORKING_MEMORY_TOKENS = 500
RECENT_MESSAGE_COUNT = 5

def build_working_memory(recent_messages: list[dict], current_query: str) -> str:
    """
    Builds the working memory string from recent messages.
    Always reserves 100 tokens for the current query.
    """
    query_tokens = count_tokens(current_query)
    available = MAX_WORKING_MEMORY_TOKENS - query_tokens - 50  # 50 token buffer

    context = ""
    for msg in reversed(recent_messages[-RECENT_MESSAGE_COUNT:]):
        candidate = f"{msg['sender']}: {truncate_message(msg['content'])}\n"
        if count_tokens(context + candidate) > available:
            break
        context = candidate + context

    return f"{context}\nCurrent Query: {current_query}"
```

---

### Layer 2: Episodic Memory (Vector Database)
**Purpose**: What happened in PAST SESSIONS — long-term semantic search.  
**Storage**: Vector database (Chroma — embedded, no separate server, free).  
**Update cadence**: Every message, asynchronously.  
**Query method**: Cosine similarity search, returns top-K chunks.

**Step 1 — Install Chroma**:
```bash
pip install chromadb
```

**Step 2 — Create** `app/memory/episodic_memory.py`:
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(path="./chroma_db")

def get_collection(room_id: str):
    return client.get_or_create_collection(
        name=f"room_{room_id}",
        metadata={"hnsw:space": "cosine"}
    )

def store_message(room_id: str, message_id: str, content: str, metadata: dict):
    """Store a message chunk into the vector DB asynchronously."""
    collection = get_collection(room_id)
    # Chunk message if it exceeds 200 tokens
    chunks = chunk_text(content, max_tokens=200)
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[f"{message_id}_chunk_{i}"],
            metadatas=[{**metadata, "chunk_index": i}]
        )

def retrieve_relevant(room_id: str, query: str, top_k: int = 5, token_budget: int = 600) -> str:
    """
    Retrieve semantically relevant past messages within token budget.
    Returns formatted string, never exceeds token_budget.
    """
    collection = get_collection(room_id)
    results = collection.query(query_texts=[query], n_results=top_k)

    context = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        candidate = f"[{meta.get('sender', 'Unknown')}]: {doc}\n"
        if count_tokens(context + candidate) > token_budget:
            break
        context += candidate

    return context
```

---

### Layer 3: Semantic Memory (Knowledge Graph)
**Purpose**: What the team KNOWS and HAS DECIDED — entities, relationships, conclusions.  
**Storage**: Kuzu (embedded graph DB, like SQLite but for graphs — no server needed).  
**Update cadence**: After every AI synthesis, asynchronously.  
**Query method**: Graph traversal by entity or relationship type.

**Step 1 — Install Kuzu**:
```bash
pip install kuzu
```

**Step 2 — Create** `app/memory/semantic_memory.py`:
```python
import kuzu

db = kuzu.Database("./kuzu_db")
conn = kuzu.Connection(db)

def initialize_schema():
    """Run once at startup."""
    conn.execute("CREATE NODE TABLE IF NOT EXISTS Entity(id STRING, type STRING, content STRING, room_id STRING, PRIMARY KEY(id))")
    conn.execute("CREATE NODE TABLE IF NOT EXISTS Decision(id STRING, content STRING, room_id STRING, timestamp STRING, PRIMARY KEY(id))")
    conn.execute("CREATE REL TABLE IF NOT EXISTS RELATES_TO(FROM Entity TO Entity, relationship STRING)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS LED_TO(FROM Entity TO Decision)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS CONTRADICTS(FROM Decision TO Decision, reason STRING)")

def write_memory_packet(room_id: str, memory_writes: dict):
    """
    Called after every synthesis. Writes decisions, entities, relationships.
    This runs asynchronously — does not block the response stream.
    
    memory_writes = {
        "new_decisions": [...],
        "new_entities": [...],
        "new_relationships": [...],
        "contradictions": [...]
    }
    """
    for decision in memory_writes.get("new_decisions", []):
        conn.execute(
            "MERGE (d:Decision {id: $id, content: $content, room_id: $room_id, timestamp: $ts})",
            {"id": generate_id(), "content": decision, "room_id": room_id, "ts": now()}
        )
    # ... write entities and relationships similarly

def retrieve_related(room_id: str, query: str, token_budget: int = 400) -> str:
    """
    Traverse graph to find decisions and entities related to the query topic.
    Returns formatted string within token budget.
    """
    # Extract key terms from query for graph lookup
    key_terms = extract_key_terms(query)  # simple noun extraction
    
    results = []
    for term in key_terms:
        res = conn.execute(
            """MATCH (d:Decision) 
               WHERE d.room_id = $room_id AND d.content CONTAINS $term
               RETURN d.content LIMIT 5""",
            {"room_id": room_id, "term": term}
        ).get_as_df()
        results.extend(res["d.content"].tolist())

    context = "Past Decisions:\n"
    for r in results:
        candidate = f"- {r}\n"
        if count_tokens(context + candidate) > token_budget:
            break
        context += candidate

    return context

def check_contradictions(room_id: str, new_claim: str) -> list[str]:
    """
    Check if a new claim contradicts existing decisions in the graph.
    Used by proactive invocation system.
    """
    # Query graph for decisions on same topic, return contradicting ones
    pass
```

---

### Layer 4: Procedural Memory (Structured DB)
**Purpose**: How the team works — member expertise, preferences, recurring patterns.  
**Storage**: Your existing SQLite via SQLAlchemy (just new tables).  
**Update cadence**: Background job, weekly or after 50 messages.

**Step 1 — Add to your SQLAlchemy models**:
```python
class MemberProfile(Base):
    __tablename__ = "member_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("groups.id"))
    
    # Expertise signals extracted from past messages
    domain_signals = Column(JSON)  # {"frontend": 0.8, "databases": 0.3}
    
    # Communication style
    prefers_concise = Column(Boolean, default=False)
    technical_depth = Column(Float, default=0.5)  # 0=beginner, 1=expert
    
    # Contribution patterns
    message_count = Column(Integer, default=0)
    avg_message_length = Column(Float, default=0)
    topics_discussed = Column(JSON)  # list of topic strings
    
    updated_at = Column(DateTime)

class RoomPreferences(Base):
    __tablename__ = "room_preferences"
    
    room_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)
    preferred_ai_depth = Column(String, default="medium")  # low/medium/high
    dominant_topics = Column(JSON)
    active_hours = Column(JSON)  # when team is most active
    updated_at = Column(DateTime)
```

**Step 2 — Create** `app/memory/procedural_memory.py`:
```python
def get_member_context(user_id: int, room_id: int, token_budget: int = 200) -> str:
    """Returns a small member context string for personalizing AI response."""
    profile = db.query(MemberProfile).filter_by(user_id=user_id, room_id=room_id).first()
    if not profile:
        return ""
    
    lines = []
    if profile.technical_depth > 0.7:
        lines.append("Member is highly technical — use precise terminology.")
    elif profile.technical_depth < 0.3:
        lines.append("Member prefers simple explanations — avoid jargon.")
    if profile.prefers_concise:
        lines.append("Member prefers concise answers.")
    
    return "\n".join(lines)

def update_member_profile(user_id: int, room_id: int, message: str):
    """Called async after every message. Updates signals gradually."""
    # Run as background task, never blocks message flow
    pass
```

---

## Phase 2 — Token Budget Enforcement

### What You're Building
A single utility module that every other module uses. No component ever exceeds its assigned token budget.

**Create** `app/utils/token_budget.py`:
```python
import tiktoken

# Use cl100k_base tokenizer (works for all major LLMs as approximation)
enc = tiktoken.get_encoding("cl100k_base")

# ─── Global Pipeline Budget ────────────────────────────────────────────────
TOTAL_PIPELINE_BUDGET = 4000  # tokens

BUDGETS = {
    "gatekeeper":    300,   # last 3 msgs + query only
    "working":       500,   # current thread context
    "episodic":      600,   # vector search results
    "semantic":      400,   # knowledge graph results
    "procedural":    200,   # member profile context
    "agent_each":    800,   # what each agent receives
    "synthesis":     600,   # synthesis receives agent outputs only
    "buffer":        200,
}
# Total: 300+500+600+400+200 = 2000 for memory assembly
# Each agent: 800 (but agents run parallel, not additive in cost)

# ─── Per-Message Hard Cap ─────────────────────────────────────────────────
MAX_TOKENS_PER_MESSAGE = 300

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

def truncate_to_budget(text: str, budget: int) -> str:
    """Hard truncate text to token budget. Never exceeds budget."""
    tokens = enc.encode(text)
    if len(tokens) <= budget:
        return text
    return enc.decode(tokens[:budget]) + "... [truncated]"

def truncate_message(message: str) -> str:
    """Apply per-message hard cap. Call at write time."""
    return truncate_to_budget(message, MAX_TOKENS_PER_MESSAGE)

def chunk_text(text: str, max_tokens: int) -> list[str]:
    """Split text into chunks, each within max_tokens."""
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunks.append(enc.decode(chunk_tokens))
    return chunks

def recursive_summarize(chunks: list[str], summarizer_llm, budget: int = 200) -> str:
    """
    Summarize list of text chunks recursively.
    Summarizer never receives more than BUDGETS['episodic'] tokens at once.
    """
    if not chunks:
        return ""
    
    summaries = []
    for chunk in chunks:
        summary = summarizer_llm.summarize(
            truncate_to_budget(chunk, 1000),  # summarizer input cap
            max_output_tokens=budget
        )
        summaries.append(truncate_to_budget(summary, budget))
    
    # If combined summaries still too large, recurse
    combined = "\n".join(summaries)
    if count_tokens(combined) > budget * 2:
        return recursive_summarize(summaries, summarizer_llm, budget)
    
    return combined
```

**Apply truncation at write time** in your message save endpoint:
```python
# In your WebSocket message handler, before saving to DB:
from app.utils.token_budget import truncate_message

@router.websocket("/api/ws/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: int):
    # ... existing code ...
    message_content = truncate_message(data["content"])  # Add this line
    # then save to DB as normal
```

---

## Phase 3 — Unified Gatekeeper + Router

### What You're Replacing
Two sequential LLM calls: `gatekeeper check` → `intent_classifier`. Both receive full context.

### What You're Building
One LLM call, last 3 messages only, returns full routing packet.

**Rewrite** `app/agents/intent_classifier.py` → rename to `app/agents/gatekeeper_router.py`:

```python
from app.utils.token_budget import truncate_to_budget, BUDGETS

GATEKEEPER_SYSTEM_PROMPT = """
You are a routing agent for a collaborative AI workspace.
Analyze the last few messages and return ONLY a JSON object.

Respond ONLY with this exact JSON structure, no other text:
{
  "should_intervene": true or false,
  "mode": "divergent" or "convergent" or "adversarial" or null,
  "trigger_type": "explicit" or "implicit" or "skip",
  "relevant_layers": ["episodic", "semantic", "procedural"] (subset, can be empty),
  "complexity": "simple" or "complex",
  "reasoning_hint": "one sentence about what the query needs"
}

Rules:
- should_intervene = false if humans are casually chatting, greeting, or discussing logistics
- should_intervene = true if there is a question, a factual claim, a comparison, a debate, or a request for explanation
- mode = "divergent" for brainstorming, comparisons, option generation
- mode = "convergent" for explanations, deep dives, step-by-step reasoning
- mode = "adversarial" for fact-checking, controversial claims, risk assessment
- relevant_layers: include "episodic" if query references past events; "semantic" if it references decisions; "procedural" if member expertise matters
"""

async def route_message(last_3_messages: list[dict], current_query: str) -> dict:
    """
    Single LLM call. Replaces both gatekeeper and intent_classifier.
    Receives only last 3 messages — never full context.
    """
    # Build minimal context (hard capped to BUDGETS['gatekeeper'])
    mini_context = ""
    for msg in last_3_messages[-3:]:
        line = f"{msg['sender']}: {msg['content']}\n"
        mini_context += line
    
    mini_context = truncate_to_budget(mini_context, BUDGETS["gatekeeper"] - 50)
    
    prompt = f"""Recent messages:
{mini_context}

New message: {current_query}

Return routing JSON:"""

    response = await llm_call(
        model="llama-3.1-8b-instant",  # Use fastest/cheapest model here
        system=GATEKEEPER_SYSTEM_PROMPT,
        user=prompt,
        max_tokens=150  # Routing packet is always small
    )
    
    try:
        routing = json.loads(response)
        return routing
    except json.JSONDecodeError:
        # Safe fallback
        return {"should_intervene": False, "mode": None, "trigger_type": "skip"}
```

---

## Phase 4 — Memory Assembly Service

### What You're Building
A single service that assembles the memory packet ONCE per invocation. All agents receive the same pre-assembled packet — context is never rebuilt or re-fetched per agent.

**Create** `app/memory/memory_assembler.py`:

```python
from app.memory.working_memory import build_working_memory
from app.memory.episodic_memory import retrieve_relevant
from app.memory.semantic_memory import retrieve_related
from app.memory.procedural_memory import get_member_context
from app.utils.token_budget import BUDGETS, count_tokens
import asyncio

async def assemble_memory_packet(
    room_id: int,
    user_id: int,
    current_query: str,
    recent_messages: list[dict],
    relevant_layers: list[str]  # from gatekeeper routing packet
) -> dict:
    """
    Assembles all memory layers in parallel.
    Returns a fixed-size memory packet — never exceeds total budget.
    This is called ONCE per invocation. All agents share this packet.
    """
    
    # Fetch layers in parallel — only the layers gatekeeper flagged as relevant
    tasks = {
        "working": build_working_memory(recent_messages, current_query),
    }
    
    if "episodic" in relevant_layers:
        tasks["episodic"] = retrieve_relevant(
            room_id, current_query, token_budget=BUDGETS["episodic"]
        )
    if "semantic" in relevant_layers:
        tasks["semantic"] = retrieve_related(
            room_id, current_query, token_budget=BUDGETS["semantic"]
        )
    if "procedural" in relevant_layers:
        tasks["procedural"] = get_member_context(
            user_id, room_id, token_budget=BUDGETS["procedural"]
        )
    
    # Run all fetches in parallel
    results = {}
    async_tasks = {k: v for k, v in tasks.items() if asyncio.iscoroutine(v)}
    sync_results = {k: v for k, v in tasks.items() if not asyncio.iscoroutine(v)}
    
    gathered = await asyncio.gather(*async_tasks.values(), return_exceptions=True)
    for key, result in zip(async_tasks.keys(), gathered):
        results[key] = result if not isinstance(result, Exception) else ""
    results.update(sync_results)
    
    # Assemble into single formatted string
    packet_parts = []
    
    if results.get("semantic"):
        packet_parts.append(f"=== Team Knowledge & Decisions ===\n{results['semantic']}")
    if results.get("episodic"):
        packet_parts.append(f"=== Relevant Past Context ===\n{results['episodic']}")
    if results.get("procedural"):
        packet_parts.append(f"=== Member Context ===\n{results['procedural']}")
    if results.get("working"):
        packet_parts.append(f"=== Current Thread ===\n{results['working']}")
    
    assembled = "\n\n".join(packet_parts)
    
    return {
        "assembled_context": assembled,
        "query": current_query,
        "layers_used": list(results.keys()),
        "token_count": count_tokens(assembled)
    }
```

---

## Phase 5 — Restructured Agent Modes

### What Changes
- Agents receive `memory_packet["assembled_context"]` — NOT raw conversation history
- Independent/Support modes run with `asyncio.gather()` (parallel)
- Adversarial mode capped at 2 rounds with early exit
- Each mode uses **structurally enforced diversity**, not emergent diversity

---

### Mode 1: Divergent (Replaces Independent)

**Create** `app/agents/modes/divergent_mode.py`:
```python
async def run_divergent(memory_packet: dict) -> list[dict]:
    """
    Three agents forced to reason from DIFFERENT AXIOMS.
    Runs fully in parallel.
    """
    context = memory_packet["assembled_context"]
    query = memory_packet["query"]
    
    # Structurally enforced diversity — different constraints per agent
    agent_configs = [
        {
            "name": "Workspace-Grounded",
            "instruction": "Answer using ONLY information present in the team context provided. Do not use external knowledge.",
            "model": "llama-3.3-70b-versatile"
        },
        {
            "name": "Best-Case",
            "instruction": "Answer assuming ideal conditions, best available tools, and no resource constraints.",
            "model": "llama-3.3-70b-versatile"
        },
        {
            "name": "Constraint-Aware",
            "instruction": "Answer assuming real-world constraints: limited time, potential team disagreements, technical debt.",
            "model": "llama-3.1-8b-instant"
        }
    ]
    
    async def run_agent(config: dict) -> dict:
        response = await llm_call(
            model=config["model"],
            system=f"You are the {config['name']} perspective agent. {config['instruction']}",
            user=f"Team Context:\n{context}\n\nQuery: {query}",
            max_tokens=400
        )
        return {"agent": config["name"], "response": response}
    
    # ALL THREE run in parallel — critical for latency
    results = await asyncio.gather(
        run_agent(agent_configs[0]),
        run_agent(agent_configs[1]),
        run_agent(agent_configs[2])
    )
    
    return list(results)
```

---

### Mode 2: Convergent (Replaces Support)

**Create** `app/agents/modes/convergent_mode.py`:
```python
async def run_convergent(memory_packet: dict) -> list[dict]:
    """
    Agent 1 builds the answer. Agent 2 runs consistency checks in parallel.
    Agent 2 does NOT see Agent 1's output — checks against context only.
    This prevents echo chamber while maintaining depth.
    """
    context = memory_packet["assembled_context"]
    query = memory_packet["query"]
    
    async def primary_agent():
        return await llm_call(
            model="llama-3.3-70b-versatile",
            system="You are the primary explainer. Give a thorough, structured answer.",
            user=f"Context:\n{context}\n\nQuery: {query}",
            max_tokens=500
        )
    
    async def consistency_checker():
        """
        Independently identifies what a complete answer MUST contain.
        Synthesis uses this to verify the primary agent didn't miss anything.
        """
        return await llm_call(
            model="llama-3.1-8b-instant",
            system="List the key points any complete answer to this query must cover. Be brief.",
            user=f"Context:\n{context}\n\nQuery: {query}",
            max_tokens=150
        )
    
    # Run both in parallel
    primary_response, checklist = await asyncio.gather(
        primary_agent(),
        consistency_checker()
    )
    
    return [
        {"agent": "Primary", "response": primary_response},
        {"agent": "Checklist", "response": checklist}
    ]
```

---

### Mode 3: Adversarial (Replaces Opposition)

**Create** `app/agents/modes/adversarial_mode.py`:
```python
async def run_adversarial(memory_packet: dict) -> list[dict]:
    """
    Structured as a legal proceeding. Maximum 2 rounds. Early exit if confidence high.
    Round structure: Prosecutor → Defense → Expert Witness (graph) → Judge verdict
    """
    context = memory_packet["assembled_context"]
    query = memory_packet["query"]
    debate_log = []
    
    # Round 1: Prosecutor and Defense run in PARALLEL (they don't need each other's output)
    prosecutor_prompt = f"Make the strongest possible case FOR this position. Be specific.\nContext:\n{context}\nClaim: {query}"
    defense_prompt = f"Make the strongest possible case AGAINST this position. Be specific.\nContext:\n{context}\nClaim: {query}"
    
    prosecution, defense = await asyncio.gather(
        llm_call(model="llama-3.3-70b-versatile", system="You are a prosecutor. Argue FOR the claim.", user=prosecutor_prompt, max_tokens=300),
        llm_call(model="llama-3.3-70b-versatile", system="You are a defense attorney. Argue AGAINST the claim.", user=defense_prompt, max_tokens=300)
    )
    
    debate_log.extend([
        {"agent": "Prosecutor", "response": prosecution},
        {"agent": "Defense", "response": defense}
    ])
    
    # Expert Witness: Pull relevant past decisions from knowledge graph
    # This grounds the debate in team history — not just model opinion
    from app.memory.semantic_memory import retrieve_related
    expert_evidence = await retrieve_related(
        memory_packet.get("room_id"), query, token_budget=300
    )
    debate_log.append({"agent": "Expert Witness (Team History)", "response": expert_evidence or "No relevant team history found."})
    
    # Judge issues verdict — receives debate log, NOT original context
    debate_summary = "\n\n".join([f"{d['agent']}: {d['response']}" for d in debate_log])
    
    # Early exit check: if prosecution and defense substantially agree, skip round 2
    agreement_check = await llm_call(
        model="llama-3.1-8b-instant",
        system="Do the prosecution and defense substantially agree? Answer only YES or NO.",
        user=f"Prosecution: {prosecution}\n\nDefense: {defense}",
        max_tokens=5
    )
    
    if "YES" in agreement_check.upper():
        # Skip round 2, go straight to verdict
        pass
    else:
        # Round 2: Rebuttals (only if genuine disagreement)
        prosecutor_rebuttal, defense_rebuttal = await asyncio.gather(
            llm_call(model="llama-3.1-8b-instant", system="Brief rebuttal only.", 
                     user=f"Defense argued: {defense}\nYour rebuttal:", max_tokens=150),
            llm_call(model="llama-3.1-8b-instant", system="Brief rebuttal only.",
                     user=f"Prosecution argued: {prosecution}\nYour rebuttal:", max_tokens=150)
        )
        debate_log.extend([
            {"agent": "Prosecutor Rebuttal", "response": prosecutor_rebuttal},
            {"agent": "Defense Rebuttal", "response": defense_rebuttal}
        ])
        debate_summary = "\n\n".join([f"{d['agent']}: {d['response']}" for d in debate_log])
    
    # Judge verdict
    verdict = await llm_call(
        model="llama-3.3-70b-versatile",
        system="""You are the Chief Judge. Review the debate and expert evidence.
Issue a verdict: state which position is better supported and why.
Be definitive. If inconclusive, say so explicitly.""",
        user=f"Debate Record:\n{debate_summary}",
        max_tokens=300
    )
    
    debate_log.append({"agent": "Judge Verdict", "response": verdict})
    return debate_log
```

---

## Phase 6 — Synthesis Engine as a Write Operation

### What Changes
The synthesis engine now does TWO things:
1. Streams the response to the user (same as before)
2. Produces a `memory_writes` packet that updates the knowledge graph asynchronously

**Rewrite** `app/orchestrator.py`:
```python
SYNTHESIS_SYSTEM_PROMPT = """
You are the Master Synthesis Engine for a collaborative team workspace.

You receive outputs from specialized agents. Your job:
1. Synthesize the best response for the team
2. Extract knowledge to update team memory

Respond with ONLY this JSON structure:
{
  "response": "The full synthesized response to stream to users",
  "memory_writes": {
    "new_decisions": ["list of decisions or conclusions reached"],
    "new_entities": [{"name": "...", "type": "concept|tool|person|project"}],
    "new_relationships": [{"from": "...", "via": "relates-to|contradicts|supports|led-to", "to": "..."}],
    "open_questions": ["questions that remain unresolved"],
    "contradictions_found": ["any contradictions with team history"]
  }
}

Rules:
- response: synthesize what agents said. Drop hallucinated or unsupported claims.
- memory_writes: only include things that were actually established in the agent outputs
- If agents substantially agree, say so clearly
- If agents disagree, present the disagreement honestly
"""

async def synthesize_and_write(
    agent_outputs: list[dict],
    room_id: int,
    websocket_manager,
    room_clients: list
) -> str:
    """
    Receives ONLY agent outputs — never the original context.
    Streams response immediately. Writes memory asynchronously.
    """
    
    # Format agent outputs for synthesis (no context passed here)
    agent_summary = "\n\n".join([
        f"=== {a['agent']} ===\n{a['response']}"
        for a in agent_outputs
    ])
    
    # Get synthesis from master engine
    raw_response = await llm_call(
        model="llama-3.3-70b-versatile",
        system=SYNTHESIS_SYSTEM_PROMPT,
        user=f"Agent Outputs:\n{agent_summary}",
        max_tokens=800
    )
    
    try:
        synthesis = json.loads(raw_response)
        user_response = synthesis["response"]
        memory_writes = synthesis.get("memory_writes", {})
    except json.JSONDecodeError:
        user_response = raw_response
        memory_writes = {}
    
    # 1. Stream response to users immediately (non-blocking)
    asyncio.create_task(
        stream_response_to_clients(user_response, room_clients, websocket_manager)
    )
    
    # 2. Write to knowledge graph asynchronously (does not block stream)
    if memory_writes:
        asyncio.create_task(
            write_memory_async(room_id, memory_writes)
        )
    
    return user_response

async def write_memory_async(room_id: int, memory_writes: dict):
    """Runs in background. Never blocks user-facing response."""
    from app.memory.semantic_memory import write_memory_packet
    try:
        write_memory_packet(room_id, memory_writes)
    except Exception as e:
        # Log but never raise — memory write failure should not affect user experience
        logger.error(f"Memory write failed for room {room_id}: {e}")
```

---

## Phase 7 — Proactive AI Invocation

### What You're Building
A background monitor that watches for situations where the AI should intervene WITHOUT being asked. Enabled by the knowledge graph.

**Create** `app/agents/proactive_monitor.py`:
```python
class ProactiveMonitor:
    """
    Runs as a background task. Monitors messages for proactive intervention opportunities.
    Triggers are based on knowledge graph, not message content alone.
    """
    
    PROACTIVE_TRIGGERS = [
        "contradiction",    # New message contradicts past decision
        "unanswered",       # Question asked by human, not answered for 5+ minutes
        "pattern",          # Recurring topic that team has struggled with before
    ]
    
    async def check_message(self, room_id: int, message: dict, websocket_manager):
        """Called async after every message. Never blocks the message flow."""
        
        checks = await asyncio.gather(
            self._check_contradiction(room_id, message),
            self._check_unanswered_question(room_id, message),
            return_exceptions=True
        )
        
        for check in checks:
            if isinstance(check, dict) and check.get("should_intervene"):
                await self._trigger_proactive_response(
                    room_id, check, websocket_manager
                )
                break  # Only one proactive intervention per message
    
    async def _check_contradiction(self, room_id: int, message: dict) -> dict:
        """Check if message contradicts existing knowledge graph decisions."""
        from app.memory.semantic_memory import check_contradictions
        
        contradictions = check_contradictions(room_id, message["content"])
        if contradictions:
            return {
                "should_intervene": True,
                "type": "contradiction",
                "detail": contradictions[0],
                "message": f"⚠️ This may contradict a previous team decision: '{contradictions[0]}'. Want me to help reconcile this?"
            }
        return {"should_intervene": False}
    
    async def _check_unanswered_question(self, room_id: int, message: dict) -> dict:
        """Check if a question was asked but not answered for 5+ minutes."""
        # Simple heuristic: message ends with '?' and no response for 300 seconds
        if message["content"].strip().endswith("?"):
            await asyncio.sleep(300)  # Wait 5 minutes
            # Check if question was answered in the interim
            recent = get_messages_since(room_id, message["timestamp"])
            if len(recent) == 0:
                return {
                    "should_intervene": True,
                    "type": "unanswered",
                    "message": "I noticed this question hasn't been answered yet. Want me to help?"
                }
        return {"should_intervene": False}
    
    async def _trigger_proactive_response(self, room_id: int, trigger: dict, websocket_manager):
        """Send proactive AI message to room."""
        await websocket_manager.broadcast(room_id, {
            "type": "proactive_ai",
            "sender": "AI Monitor",
            "content": trigger["message"],
            "trigger_type": trigger["type"]
        })

# Register in your FastAPI startup
proactive_monitor = ProactiveMonitor()
```

---

## Phase 8 — Member-Aware Context

### What You're Building
The AI's response is personalized based on who asked — technical depth, preferred brevity, domain expertise.

**Update** `app/orchestrator.py` synthesis prompt to include member context:
```python
async def build_member_aware_synthesis_prompt(
    agent_outputs: list[dict],
    user_id: int,
    room_id: int
) -> str:
    """
    Adds member context to synthesis so response is calibrated to the asker.
    """
    from app.memory.procedural_memory import get_member_context
    member_context = get_member_context(user_id, room_id, token_budget=100)
    
    agent_summary = "\n\n".join([f"=== {a['agent']} ===\n{a['response']}" for a in agent_outputs])
    
    return f"""Agent Outputs:
{agent_summary}

Responding To:
{member_context}

Calibrate the depth, terminology, and length of your response accordingly."""
```

**Add background profile updater** in your message save flow:
```python
# After saving message to DB, fire and forget:
async def on_message_saved(user_id: int, room_id: int, content: str):
    asyncio.create_task(
        update_member_profile_async(user_id, room_id, content)
    )

async def update_member_profile_async(user_id: int, room_id: int, content: str):
    """
    Updates member signals gradually. Uses simple heuristics, not LLM calls.
    """
    profile = get_or_create_profile(user_id, room_id)
    
    # Technical depth signal: presence of technical terms
    technical_terms = ["API", "database", "async", "algorithm", "schema", "latency"]
    tech_score = sum(1 for term in technical_terms if term.lower() in content.lower())
    
    # Gradually update (exponential moving average, not hard overwrite)
    alpha = 0.1  # Learning rate
    profile.technical_depth = (1 - alpha) * profile.technical_depth + alpha * min(tech_score / 3, 1.0)
    profile.message_count += 1
    
    db.commit()
```

---

## Phase 9 — Session Closing Report

### What You're Building
A background job that fires when a session goes quiet. Produces a structured digest of what happened.

**Create** `app/jobs/session_reporter.py`:
```python
INACTIVITY_THRESHOLD = 30 * 60  # 30 minutes of silence = session ended

async def check_session_end(room_id: int, last_activity: datetime, websocket_manager):
    """Called by a scheduler every 5 minutes per active room."""
    silence_duration = (datetime.now() - last_activity).seconds
    
    if silence_duration >= INACTIVITY_THRESHOLD:
        report = await generate_session_report(room_id)
        await websocket_manager.broadcast(room_id, {
            "type": "session_report",
            "sender": "AI Workspace",
            "content": report
        })

async def generate_session_report(room_id: int) -> str:
    """
    Pulls from knowledge graph — specifically the memory_writes 
    that were added during this session.
    """
    from app.memory.semantic_memory import get_session_writes
    
    session_data = get_session_writes(room_id, since=session_start_time(room_id))
    
    report_prompt = f"""
Generate a brief session closing report for this team workspace session.

Data from this session:
{json.dumps(session_data, indent=2)}

Format:
## Session Summary
**Decisions Made**: [list]
**Open Questions**: [list]  
**Key Topics Discussed**: [list]
**Recommended Next Steps**: [list]

Keep each section to 2-3 bullet points maximum.
"""
    
    report = await llm_call(
        model="llama-3.1-8b-instant",  # Fast model, simple task
        system="You generate concise workspace session reports.",
        user=report_prompt,
        max_tokens=300
    )
    
    return report

# Register with APScheduler in your FastAPI startup:
# pip install apscheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        check_all_active_rooms,
        "interval",
        minutes=5
    )
    scheduler.start()
```

---

## Phase 10 — Evaluation Suite Upgrade

### What Changes
Add two new metrics that matter for the new architecture:

**1. Memory Utilization Score** — Did the AI actually use the knowledge graph?
```python
def memory_utilization_score(response: str, semantic_context: str) -> float:
    """
    Measures how much of the knowledge graph context was incorporated.
    Prevents the AI from ignoring team history.
    """
    if not semantic_context:
        return 1.0  # No memory to use, trivially satisfied
    
    graph_entities = extract_key_terms(semantic_context)
    response_terms = extract_key_terms(response)
    
    overlap = len(set(graph_entities) & set(response_terms))
    return overlap / max(len(graph_entities), 1)
```

**2. Contradiction Rate** — Did the AI contradict existing team decisions?
```python
async def contradiction_rate(response: str, room_id: int) -> float:
    """
    Checks if the AI response contradicts knowledge graph decisions.
    Returns 0.0 (no contradictions) to 1.0 (fully contradictory).
    """
    from app.memory.semantic_memory import check_contradictions
    contradictions = check_contradictions(room_id, response)
    
    if not contradictions:
        return 0.0
    
    # LLM judge: are these real contradictions or just surface-level similarity?
    judgment = await llm_call(
        model="llama-3.1-8b-instant",
        system="Count how many genuine logical contradictions exist. Return only a number 0-5.",
        user=f"New statement: {response}\n\nPotential contradictions: {contradictions}",
        max_tokens=5
    )
    
    return min(int(judgment.strip()) / 5, 1.0)
```

---

## Implementation Order & Timeline

Do NOT implement everything at once. Follow this sequence — each phase is independently deployable and testable.

```
Week 1-2: Foundation
├── Phase 2  → Token Budget Enforcement (no functional change, just safety)
└── Phase 3  → Unified Gatekeeper + Router (reduces LLM calls immediately)

Week 3-4: Memory Infrastructure  
├── Phase 1  → Layer 1 (Working Memory — replace existing context_builder)
└── Phase 1  → Layer 2 (Episodic Memory — add Chroma, run alongside existing)

Week 5-6: Knowledge Graph
├── Phase 1  → Layer 3 (Semantic Memory — add Kuzu)
└── Phase 6  → Synthesis as Write Operation (start populating graph)

Week 7-8: Agent Restructure
├── Phase 4  → Memory Assembly Service
├── Phase 5  → Divergent Mode (parallel agents)
├── Phase 5  → Convergent Mode (consistency checker)
└── Phase 5  → Adversarial Mode (2 rounds, early exit, expert witness)

Week 9-10: Intelligence Layer
├── Phase 7  → Proactive Invocation (contradiction detection first)
├── Phase 8  → Member-Aware Context
└── Phase 9  → Session Closing Report

Week 11: Evaluation
└── Phase 10 → Add Memory Utilization and Contradiction Rate metrics
```

---

## Folder Structure After All Changes

```
app/
├── agents/
│   ├── gatekeeper_router.py        # Replaces intent_classifier.py (unified, single call)
│   ├── proactive_monitor.py        # NEW: background contradiction + unanswered detection
│   └── modes/
│       ├── divergent_mode.py       # Replaces independent (parallel, axiom-enforced)
│       ├── convergent_mode.py      # Replaces support (primary + consistency checker)
│       └── adversarial_mode.py     # Replaces opposition (2 rounds, legal structure)
│
├── memory/
│   ├── working_memory.py           # NEW: last 3-5 messages, hard capped
│   ├── episodic_memory.py          # NEW: Chroma vector DB, semantic retrieval
│   ├── semantic_memory.py          # NEW: Kuzu knowledge graph, decisions + entities
│   ├── procedural_memory.py        # NEW: member profiles, team preferences
│   └── memory_assembler.py         # NEW: assembles all layers ONCE per invocation
│
├── jobs/
│   └── session_reporter.py         # NEW: APScheduler, end-of-session digest
│
├── utils/
│   └── token_budget.py             # NEW: global budget enforcement, truncation, chunking
│
├── Evaluation/
│   ├── Evaluator.py                # UPDATED: add memory_utilization_score
│   ├── contradiction_evaluator.py  # NEW: checks AI response vs knowledge graph
│   └── [existing evaluators]
│
├── orchestrator.py                 # UPDATED: synthesize + async memory write
├── context_builder.py              # RETIRED: replaced by memory_assembler.py
└── [existing files unchanged]

chroma_db/                          # NEW: auto-created by Chroma
kuzu_db/                            # NEW: auto-created by Kuzu
```

---

## Key Principles to Maintain Throughout

1. **Context is assembled once, shared.** Never rebuild context per agent.
2. **Synthesis receives agent outputs only.** Never original context.
3. **Every write to DB also writes to vector DB.** Episodic memory stays current automatically.
4. **Every synthesis writes to knowledge graph.** System gets smarter passively.
5. **Async everything that doesn't affect the response.** Memory writes, profile updates, proactive checks — none block the stream.
6. **Token budgets are hard limits, not guidelines.** Enforce with truncation, never with hope.
7. **Gatekeeper uses cheapest/fastest model.** It decides routing — not reasoning. Speed matters more than intelligence here.
8. **Parallel before sequential, always.** If two agents don't need each other's output, they run simultaneously.
