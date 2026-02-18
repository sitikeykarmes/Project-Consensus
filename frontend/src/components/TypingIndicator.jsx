export default function TypingIndicator() {
  return (
    <div data-testid="typing-indicator" className="flex justify-start msg-enter">
      <div
        className="flex items-center gap-2 px-4 py-3 rounded-xl rounded-tl-none"
        style={{
          background: "#202c33",
          border: "1px solid #2a3942",
        }}
      >
        <div
          className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
          style={{ background: "#00a884", color: "#fff" }}
        >
          AI
        </div>
        <div className="flex gap-1 items-center h-5">
          <span className="typing-dot w-2 h-2 rounded-full inline-block" style={{ background: "#8696a0" }} />
          <span className="typing-dot w-2 h-2 rounded-full inline-block" style={{ background: "#8696a0" }} />
          <span className="typing-dot w-2 h-2 rounded-full inline-block" style={{ background: "#8696a0" }} />
        </div>
        <span className="text-xs ml-1" style={{ color: "#8696a0" }}>AI is thinking...</span>
      </div>
    </div>
  );
}
