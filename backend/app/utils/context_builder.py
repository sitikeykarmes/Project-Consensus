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
RECENT_WINDOW    = 15   # verbatim messages always shown to AI
SUMMARY_TRIGGER  = 10   # generate a new summary after every N summarizable messages
# ────────────────────────────────────────────────────────────────────────────────

_llm_client = LLMAgentClient()


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
        print(f"⏭️  Summary not triggered yet (need {SUMMARY_TRIGGER - summarizable} more messages).")
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

    msgs_to_summarize = all_msgs[:-RECENT_WINDOW] if len(all_msgs) > RECENT_WINDOW else all_msgs

    if not msgs_to_summarize:
        print("⚠️  No messages to summarize.")
        return

    convo_text = "\n".join([
        f"{m.sender_name}: {m.content}"
        for m in msgs_to_summarize
    ])

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
    """Call agent4 (Qwen) to produce a compressed context summary."""

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

    return _llm_client.get_completion("agent4", messages, max_tokens=1200)