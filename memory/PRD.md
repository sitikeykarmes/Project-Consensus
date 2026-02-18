# AgentChat - Multi-Agent AI Collaboration Platform

## Original Problem Statement
Multi-user, multi-agent chat platform with orchestrating layer. Users create groups adding AI agents and users. Uses 4 AI LLMs: intent classifier + 3 mode agents (independent, support, opposition). Consensus is synthesized from agent responses.

**Requested Changes:**
1. Typing bubble while AIs respond (WhatsApp-style)
2. Show only consensus with mode tag, with dropdown to see all agent responses
3. Implement conversation context memory for previous messages
4. Professional WhatsApp-style dark UI upgrade

## Architecture
- **Frontend**: React 19 + Vite 7 + TailwindCSS 4 + Lucide React
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **AI**: GROQ API with 4 models:
  - Intent classifier: llama-3.3-70b-versatile
  - Agent 1: openai/gpt-oss-120b
  - Agent 2: meta-llama/llama-4-scout-17b-16e-instruct
  - Agent 3: moonshotai/kimi-k2-instruct-0905
- **Real-time**: WebSocket for live chat

## User Personas
- Developers/teams wanting AI-assisted group discussions
- Users who need multi-perspective AI answers

## Core Requirements
- Multi-user authentication (JWT)
- Group creation with AI agent selection
- Real-time messaging via WebSocket
- AI orchestration: intent classification → mode execution → consensus
- Typing indicator during AI processing
- Consensus-only display with expandable agent responses
- Conversation context memory (sliding window of last 10 messages)

## What's Been Implemented (2026-02-18)
1. **Typing Indicator**: Bouncing dots animation while AI processes (WhatsApp-style)
2. **Consensus Message Bundle**: Single message showing AI consensus with mode tag (Supplement/Comparison/Debate)
3. **Expandable Agent Responses**: "See all responses" dropdown within consensus bubble
4. **Context Memory**: Sliding window of last 10 messages passed to all agents for context-aware responses
5. **Professional Dark UI**: Complete WhatsApp-inspired dark theme (#0b141a base, #00a884 accents, gold consensus highlight)
6. **API Route Fixes**: All routes prefixed with /api for Kubernetes ingress
7. **DB Schema Update**: Added extra_data column for storing agent response metadata

## Prioritized Backlog
### P0 (Critical)
- All features implemented and tested

### P1 (Important)
- Markdown rendering in consensus messages (bold, code blocks)
- Message pagination / infinite scroll for long conversations
- Group settings / edit / delete

### P2 (Nice to have)
- User avatars and profile management
- File/image sharing in chat
- Export conversation history
- Agent performance metrics

## Next Tasks
- Add markdown rendering for AI responses
- Implement message search within groups
- Add notification system for new messages
- User typing indicator (for human users, not just AI)
