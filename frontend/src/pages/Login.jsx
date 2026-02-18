import { useState } from "react";
import { Lock, Mail, ArrowRight, Users, Bot, Zap } from "lucide-react";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

export default function Login({ setUser }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin() {
    if (!email.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);

    try {
      const res = await fetch(`${BASE_URL}/api/auth/login`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Login failed");
        setLoading(false);
        return;
      }

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      setUser(data.user);
    } catch (err) {
      setError("Server connection failed");
    }
    setLoading(false);
  }

  async function handleSignup() {
    if (!email.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);
    setError("");

    try {
      const res = await fetch(
        `${BASE_URL}/auth/signup?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
        { method: "POST" }
      );

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Signup failed");
        setLoading(false);
        return;
      }

      // Auto-login after signup
      await handleLogin();
    } catch (err) {
      setError("Server connection failed");
    }
    setLoading(false);
  }

  function handleKeyPress(e) {
    if (e.key === "Enter") {
      isSignup ? handleSignup() : handleLogin();
    }
  }

  return (
    <div
      data-testid="login-page"
      className="h-screen w-screen flex items-center justify-center"
      style={{ background: "linear-gradient(135deg, #0b141a 0%, #111b21 50%, #0b141a 100%)" }}
    >
      <div className="w-full max-w-[420px] mx-4">
        {/* Logo / Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4" style={{ background: "#00a884" }}>
            <Zap size={32} color="#fff" />
          </div>
          <h1 className="text-2xl font-bold" style={{ color: "#e9edef" }}>AgentChat</h1>
          <p className="text-sm mt-1" style={{ color: "#8696a0" }}>Multi-Agent AI Collaboration</p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl p-8 shadow-2xl"
          style={{ background: "#202c33", border: "1px solid #2a3942" }}
        >
          <h2 className="text-lg font-semibold mb-6" style={{ color: "#e9edef" }}>
            {isSignup ? "Create Account" : "Welcome Back"}
          </h2>

          {error && (
            <div
              data-testid="login-error"
              className="mb-4 px-4 py-2 rounded-lg text-sm"
              style={{ background: "rgba(239,68,68,0.15)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)" }}
            >
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div className="relative">
              <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#8696a0" }} />
              <input
                data-testid="login-email-input"
                type="email"
                placeholder="Email address"
                className="w-full pl-10 pr-4 py-3 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                style={{
                  background: "#2a3942",
                  color: "#e9edef",
                  border: "1px solid #2a3942",
                  focusRingColor: "#00a884",
                }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={handleKeyPress}
              />
            </div>

            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#8696a0" }} />
              <input
                data-testid="login-password-input"
                type="password"
                placeholder="Password"
                className="w-full pl-10 pr-4 py-3 rounded-lg text-sm focus:outline-none focus:ring-2 transition-all"
                style={{
                  background: "#2a3942",
                  color: "#e9edef",
                  border: "1px solid #2a3942",
                }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={handleKeyPress}
              />
            </div>

            <button
              data-testid="login-submit-button"
              onClick={isSignup ? handleSignup : handleLogin}
              disabled={loading}
              className="w-full py-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-60"
              style={{ background: "#00a884", color: "#fff" }}
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  {isSignup ? "Sign Up" : "Log In"}
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>

          <div className="mt-6 text-center">
            <button
              data-testid="toggle-auth-mode"
              onClick={() => { setIsSignup(!isSignup); setError(""); }}
              className="text-sm transition-colors"
              style={{ color: "#00a884" }}
            >
              {isSignup ? "Already have an account? Log in" : "Don't have an account? Sign up"}
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-6 flex justify-center gap-6">
          {[
            { icon: Users, label: "Multi-User" },
            { icon: Bot, label: "AI Agents" },
            { icon: Zap, label: "Real-time" },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-1.5 text-xs" style={{ color: "#8696a0" }}>
              <Icon size={14} style={{ color: "#00a884" }} />
              {label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
