import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages, currentUser, messagesEndRef }) {
  return (
    <div className="flex-1 overflow-y-auto bg-slate-900 p-6" data-testid="chat-window">
      <div className="max-w-6xl mx-auto space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-20">
            <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center mb-4">
              <svg className="w-10 h-10 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-slate-400 mb-2">No messages yet</h3>
            <p className="text-slate-500">Start a conversation by sending a message below</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageBubble
              key={idx}
              message={msg}
              currentUser={currentUser}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
