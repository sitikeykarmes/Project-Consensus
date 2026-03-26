# backend/app/utils/context_builder.py
"""
Hybrid Context Memory
─────────────────────
  [Older messages]    →  summarized once → stored in conversation_summaries table
  [Recent N messages] →  verbatim        → fetched fresh each time

Final context fed to AI:
  ┌──────────────────────────────────────────┐
  │  SUMMARY (compressed older history)      │
  │  + RECENT 15 verbatim messages           │
  └──────────────────────────────────────────┘

Summary regenerates every SUMMARY_TRIGGER new messages beyond the recent window.
"""

import uuid
import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Message as MessageModel, ConversationSummary
from app.utils.LLM_agent_client import LLMAgentClient

# ── Config ──────────────────────────────────────────────────────────────────────
RECENT_WINDOW       = 15     # verbatim messages always shown to AI
SUMMARY_TRIGGER     = 10     # generate a new summary after every N summarizable messages
MAX_SUMMARY_CHARS   = 6000   # max characters of conversation text sent for summarization
                             # ~4 chars/token → ~1500 tokens of content
                             # leaves room for prompt overhead within Qwen's 6000 TPM limit
# ────────────────────────────────────────────────────────────────────────────────

_llm_client = LLMAgentClient()

# Fallback model order for summarization
# agent5 (Llama Scout) or agent4 (Llama 70B)
_SUMMARY_MODEL_FALLBACK = ["agent5", "agent4", "agent1"]


# ── Public API ───────────────────────────────────────────────────────────────────

def build_hybrid_context(db: Session, group_id: str) -> dict:
    """
    Returns:
        {
            "conversation_history": [...],   # list of dicts for orchestrator
            "context_str":          "...",   # formatted string for prompt injection
        }
    """
    # 1. Maybe regenerate summary
    _maybe_update_summary(db, group_id)

    # 2. Fetch recent verbatim messages
    recent_msgs = _get_recent_messages(db, group_id, limit=RECENT_WINDOW)

    # 3. Fetch stored summary
    summary_row = db.query(ConversationSummary).filter(
        ConversationSummary.group_id == group_id
    ).first()

    # 4. Build conversation_history list for orchestrator
    conversation_history = []

    if summary_row and summary_row.summary_text:
        conversation_history.append({
            "role":    "assistant",
            "name":    "Context Summary",
            "content": f"[Summary of earlier conversation]: {summary_row.summary_text}"
        })

    for msg in recent_msgs:
        if msg.sender_type == "user":
            conversation_history.append({
                "role":    "user",
                "name":    msg.sender_name,
                "content": msg.content
            })
        elif msg.sender_type == "consensus":
            conversation_history.append({
                "role":    "assistant",
                "name":    "AI Consensus",
                "content": msg.content
            })

    # 5. Build context_str for direct prompt injection
    parts = []
    if summary_row and summary_row.summary_text:
        parts.append(f"[Earlier Conversation Summary]:\n{summary_row.summary_text}")
    if recent_msgs:
        parts.append("[Recent Messages]:")
        for msg in recent_msgs:
            parts.append(f"{msg.sender_name}: {msg.content}")
    context_str = "\n".join(parts)

    return {
        "conversation_history": conversation_history,
        "context_str":          context_str,
    }


# ── Internal Helpers ─────────────────────────────────────────────────────────────

def _get_recent_messages(db: Session, group_id: str, limit: int):
    msgs = (
        db.query(MessageModel)
        .filter(MessageModel.group_id == group_id)
        .order_by(MessageModel.timestamp.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()
    return msgs


def _get_total_message_count(db: Session, group_id: str) -> int:
    return (
        db.query(MessageModel)
        .filter(
            MessageModel.group_id == group_id,
            MessageModel.sender_type.in_(["user", "consensus"])
        )
        .count()
    )


def _truncate_to_char_limit(text: str, limit: int) -> str:
    """
    Truncate conversation text to stay within character limit.
    Keeps the MOST RECENT content (bottom) since that's most relevant.
    Trims cleanly at a newline boundary so we don't cut mid-message.
    """
    if len(text) <= limit:
        return text

    truncated = text[-limit:]

    # Trim to nearest newline so we don't start mid-sentence
    first_newline = truncated.find("\n")
    if first_newline != -1:
        truncated = truncated[first_newline + 1:]

    return f"[...earlier messages truncated to fit token limit...]\n{truncated}"


def _maybe_update_summary(db: Session, group_id: str):
    """
    Trigger condition:
        messages not yet summarized (excluding recent window) >= SUMMARY_TRIGGER
    """
    total = _get_total_message_count(db, group_id)

    summary_row      = db.query(ConversationSummary).filter(
        ConversationSummary.group_id == group_id
    ).first()

    messages_covered = summary_row.messages_covered if summary_row else 0
    unsummarized     = total - messages_covered
    summarizable     = unsummarized - RECENT_WINDOW   # never summarize the recent window

    print(f"📊 [{group_id[:8]}] total={total} covered={messages_covered} "
          f"unsummarized={unsummarized} summarizable={summarizable} trigger={SUMMARY_TRIGGER}")

    if summarizable < SUMMARY_TRIGGER:
        print(f"⏭️  Summary not triggered yet "
              f"(need {SUMMARY_TRIGGER - summarizable} more messages).")
        return

    print(f"📝 Triggering summary for group {group_id[:8]} ...")

    # Fetch all messages except the recent window
    all_msgs = (
        db.query(MessageModel)
        .filter(
            MessageModel.group_id == group_id,
            MessageModel.sender_type.in_(["user", "consensus"])
        )
        .order_by(MessageModel.timestamp.asc())
        .all()
    )

    msgs_to_summarize = (
        all_msgs[:-RECENT_WINDOW] if len(all_msgs) > RECENT_WINDOW else all_msgs
    )

    if not msgs_to_summarize:
        print("⚠️  No messages to summarize.")
        return

    convo_text = "\n".join([
        f"{m.sender_name}: {m.content}"
        for m in msgs_to_summarize
    ])

    # ── Truncation removed: Llama-4-Scout has a high token limit ────────────
    # original_chars = len(convo_text)
    # convo_text     = _truncate_to_char_limit(convo_text, MAX_SUMMARY_CHARS)
    # if len(convo_text) < original_chars:
    #     print(f"✂️  Conversation truncated: {original_chars} → {len(convo_text)} chars "
    #           f"to stay within token limit.")

    existing_summary = summary_row.summary_text if summary_row else ""
    new_summary      = _generate_summary(convo_text, existing_summary)

    if not new_summary or "Error" in new_summary:
        print(f"⚠️  Summary generation failed: {new_summary}")
        return

    # Upsert
    if summary_row:
        summary_row.summary_text      = new_summary
        summary_row.messages_covered  = len(msgs_to_summarize)
        summary_row.last_message_id   = msgs_to_summarize[-1].id
        summary_row.updated_at        = datetime.utcnow()
        print(f"✅ Summary updated — now covers {len(msgs_to_summarize)} messages.")
    else:
        db.add(ConversationSummary(
            id               = str(uuid.uuid4()),
            group_id         = group_id,
            summary_text     = new_summary,
            messages_covered = len(msgs_to_summarize),
            last_message_id  = msgs_to_summarize[-1].id,
        ))
        print(f"✅ Summary created — covers {len(msgs_to_summarize)} messages.")

    db.commit()


def _generate_summary(conversation_text: str, existing_summary: str = "") -> str:
    """
    Call LLM to produce a compressed context summary.
    Tries models in fallback order if one hits rate limits or fails.
    """

    prior_section = ""
    if existing_summary:
        prior_section = f"""Previous Summary (extend/update this, don't repeat verbatim):
{existing_summary}

"""

    prompt = f"""{prior_section}New Conversation to Absorb:
{conversation_text}

Task:
Produce a concise summary (max 200 words) capturing:
- Key topics discussed
- Important facts, decisions, or conclusions reached
- Any user preferences or details mentioned
- Ongoing threads or unresolved questions

This summary will be used as memory context for an AI assistant.
Be dense and factual. No filler. Write in third-person narrative style."""

    messages = [
        {
            "role":    "system",
            "content": "You are a memory compression engine. Summarize conversations into dense, factual context for AI assistants."
        },
        {"role": "user", "content": prompt}
    ]

    # Try each model in fallback order
    for model_key in _SUMMARY_MODEL_FALLBACK:
        print(f"📝 Attempting summary with {model_key}...")
        result = _llm_client.get_completion(model_key, messages, max_tokens=600)

        # Success: no error and no rate limit message
        if result and "Error" not in result and "rate_limit_exceeded" not in result:
            print(f"✅ Summary generated using {model_key}.")
            return result

        print(f"⚠️  {model_key} failed for summary, trying next fallback...")

    return "Error: All summary models failed."