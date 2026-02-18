import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  BrainCircuit,
  Bot,
  User,
  Sparkles,
} from "lucide-react";

function getModeLabel(mode) {
  const labels = {
    independent: "Independent Mode",
    support: "Supplement Mode",
    opposition: "Debate Mode",
  };
  return labels[mode] || mode || "AI Mode";
}

function getModeColor(mode) {
  const colors = {
    independent: "#3b82f6",
    support: "#00a884",
    opposition: "#ef4444",
  };
  return colors[mode] || "#8696a0";
}

function ConsensusMessage({ msg }) {
  const [expanded, setExpanded] = useState(false);

  const modeUsed = msg.mode_used || "";
  const agentResponses = msg.agent_responses || [];
  const modeColor = getModeColor(modeUsed);

  return (
    <div
      data-testid="consensus-message"
      className="flex justify-center msg-enter"
    >
      <div
        className="w-full max-w-[85%] rounded-xl overflow-hidden consensus-glow"
        style={{
          background: "#1f2c34",
          border: "1px solid rgba(255,215,0,0.25)",
        }}
      >
        {/* Mode Header */}
        {modeUsed && (
          <div
            data-testid="consensus-mode-tag"
            className="flex items-center gap-2 px-4 py-2"
            style={{
              background: "rgba(255,215,0,0.06)",
              borderBottom: "1px solid rgba(255,215,0,0.15)",
            }}
          >
            <Sparkles size={14} style={{ color: "#FFD700" }} />
            <span
              className="text-[11px] font-bold uppercase tracking-wider"
              style={{ color: "#FFD700" }}
            >
              AI Consensus
            </span>
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{
                background: `${modeColor}22`,
                color: modeColor,
                border: `1px solid ${modeColor}44`,
              }}
            >
              {getModeLabel(modeUsed)}
            </span>
          </div>
        )}

        {/* Consensus Body */}
        <div className="px-4 py-3">
          <p
            className="text-sm leading-relaxed whitespace-pre-line"
            style={{ color: "#e9edef" }}
          >
            {msg.content}
          </p>
          {msg.timestamp && (
            <p
              className="text-[10px] mt-2 text-right"
              style={{ color: "#8696a0" }}
            >
              {new Date(msg.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          )}
        </div>

        {/* Expandable Agent Responses */}
        {agentResponses.length > 0 && (
          <>
            <button
              data-testid="see-all-responses-button"
              onClick={() => setExpanded(!expanded)}
              className="w-full py-2.5 flex items-center justify-center gap-2 transition-all cursor-pointer"
              style={{
                background: "rgba(17,27,33,0.6)",
                color: "#8696a0",
                borderTop: "1px solid rgba(42,57,66,0.5)",
              }}
            >
              <Bot size={14} />
              <span className="text-xs font-medium">
                {expanded
                  ? "Hide agent responses"
                  : `See all responses (${agentResponses.length})`}
              </span>
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {expanded && (
              <div
                data-testid="agent-responses-dropdown"
                className="px-4 py-3 space-y-3"
                style={{
                  background: "rgba(11,20,26,0.5)",
                  borderTop: "1px solid rgba(42,57,66,0.3)",
                }}
              >
                {agentResponses.map((resp, idx) => (
                  <div
                    key={idx}
                    data-testid={`agent-response-${idx}`}
                    className="rounded-lg p-3"
                    style={{
                      background: "#202c33",
                      border: "1px solid #2a3942",
                    }}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <div
                        className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold"
                        style={{ background: modeColor, color: "#fff" }}
                      >
                        {idx + 1}
                      </div>
                      <span
                        className="text-xs font-semibold"
                        style={{ color: "#e9edef" }}
                      >
                        {resp.agent_name || `Agent ${idx + 1}`}
                      </span>
                    </div>
                    <p
                      className="text-xs leading-relaxed whitespace-pre-line"
                      style={{ color: "#8696a0" }}
                    >
                      {resp.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function UserMessage({ msg, isCurrentUser }) {
  const senderLabel = isCurrentUser ? "You" : msg.sender_name || "User";

  return (
    <div
      className={`flex ${isCurrentUser ? "justify-end" : "justify-start"} msg-enter`}
    >
      <div
        data-testid={isCurrentUser ? "user-own-message" : "user-other-message"}
        className="max-w-[65%] px-4 py-2 rounded-xl shadow-sm"
        style={{
          background: isCurrentUser ? "#005c4b" : "#202c33",
          borderTopRightRadius: isCurrentUser ? 0 : undefined,
          borderTopLeftRadius: isCurrentUser ? undefined : 0,
          border: isCurrentUser ? "none" : "1px solid #2a3942",
        }}
      >
        {!isCurrentUser && (
          <p
            className="text-[11px] font-semibold mb-0.5"
            style={{ color: "#00a884" }}
          >
            {senderLabel}
          </p>
        )}
        <p
          className="text-sm leading-relaxed whitespace-pre-line"
          style={{ color: "#e9edef" }}
        >
          {msg.content}
        </p>
        {msg.timestamp && (
          <p
            className="text-[10px] mt-1 text-right"
            style={{
              color: isCurrentUser ? "rgba(255,255,255,0.5)" : "#8696a0",
            }}
          >
            {new Date(msg.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        )}
      </div>
    </div>
  );
}

function SystemMessage({ msg }) {
  return (
    <div className="flex justify-center msg-enter">
      <div
        data-testid="system-message"
        className="px-4 py-1.5 rounded-lg text-xs max-w-[70%]"
        style={{ background: "rgba(42,57,66,0.5)", color: "#8696a0" }}
      >
        {msg.content}
      </div>
    </div>
  );
}

export default function MessageBubble({ msg, currentUserId }) {
  const isCurrentUser = msg.type === "user" && msg.sender_id === currentUserId;

  if (msg.type === "consensus") {
    return <ConsensusMessage msg={msg} />;
  }

  if (msg.type === "user") {
    return <UserMessage msg={msg} isCurrentUser={isCurrentUser} />;
  }

  if (msg.type === "system" || msg.type === "agent") {
    // Legacy: handle old-style messages
    if (msg.sender_name === "Consensus" || msg.sender_name === "AI Consensus") {
      return <ConsensusMessage msg={msg} />;
    }
    return <SystemMessage msg={msg} />;
  }

  return null;
}
