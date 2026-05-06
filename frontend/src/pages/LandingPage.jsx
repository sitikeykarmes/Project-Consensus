import { Bot, Sparkles, MessageSquare, ArrowRight } from "lucide-react";

export default function LandingPage({ onLoginClick }) {
  return (
    <div className="h-screen w-screen flex flex-col" style={{ background: "var(--bg-app)", color: "var(--text-primary)", overflowY: "auto" }}>
      {/* Navigation */}
      <nav className="w-full flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--accent)" }}>
            <Bot size={24} color="#14100c" />
          </div>
          <span className="text-xl font-bold tracking-wide" style={{ color: "var(--accent)" }}>Project Consensus</span>
        </div>
        <button 
          onClick={onLoginClick}
          className="px-6 py-2.5 rounded-full font-semibold transition-all hover:-translate-y-0.5"
          style={{ background: "var(--accent)", color: "#14100c" }}
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 sm:px-8 mt-12 mb-24 max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8 text-sm" style={{ background: "var(--bg-header)", border: "1px solid var(--border)" }}>
          <Sparkles size={16} style={{ color: "var(--accent)" }} />
          <span style={{ color: "var(--text-secondary)" }}>The next generation of AI collaboration</span>
        </div>
        
        <h1 className="text-5xl sm:text-7xl font-bold mb-8 leading-tight tracking-tight">
          Achieve clarity through <br/>
          <span style={{ color: "var(--accent)" }}>Multi-Agent Consensus</span>
        </h1>
        
        <p className="text-lg sm:text-xl mb-12 max-w-2xl mx-auto leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          Watch specialized AI agents debate, collaborate, and synthesize solutions in real-time. Break down complex problems with diverse perspectives.
        </p>
        
        <button 
          onClick={onLoginClick}
          className="group flex items-center gap-3 px-8 py-4 rounded-full text-lg font-bold transition-all hover:scale-105"
          style={{ background: "var(--accent)", color: "#14100c", boxShadow: "0 10px 25px -5px rgba(212, 175, 55, 0.4)" }}
        >
          Start Collaborating
          <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
        </button>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-3 gap-6 mt-24 w-full text-left">
          {[
            { title: "Divergent Thinking", desc: "Multiple AI models brainstorm from completely different angles to generate unique solutions." },
            { title: "Adversarial Debate", desc: "Watch agents actively challenge and fact-check each other's assumptions in real-time." },
            { title: "Synthesized Output", desc: "A master agent distills the chaos into a single, cohesive, and validated final answer." }
          ].map((feature, idx) => (
            <div key={idx} className="p-6 rounded-2xl transition-all hover:-translate-y-1" style={{ background: "var(--bg-header)", border: "1px solid var(--border)" }}>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ background: "var(--bg-app)", border: "1px solid var(--border-highlight)" }}>
                <MessageSquare size={20} style={{ color: "var(--accent)" }} />
              </div>
              <h3 className="text-xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{feature.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
