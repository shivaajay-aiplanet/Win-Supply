import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState(null);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    navigate("/", { replace: true });
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="login-page h-screen w-full flex items-center justify-center relative overflow-hidden"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-blue-50/40 to-white" />

      {/* Soft gradient orbs */}
      <div className="login-orb-1 absolute w-[500px] h-[500px] rounded-full opacity-20 blur-[120px]" />
      <div className="login-orb-2 absolute w-[350px] h-[350px] rounded-full opacity-15 blur-[100px]" />

      {/* Content */}
      <div className="relative z-10 w-full max-w-[420px] px-5 login-fade-in">
        {/* Brand */}
        <div className="text-center mb-10">
          <h1
            className="text-[30px] font-semibold text-slate-800 tracking-tight mb-3"
            style={{ fontFamily: "'Outfit', sans-serif" }}
          >
            WinSupply
          </h1>
          <p className="text-[13px] text-slate-400 tracking-wide uppercase font-medium">
            Product Cross Reference AI System{" "}
            <span className="text-blue-500">by AI Planet</span>
          </p>
        </div>

        {/* Card */}
        <div className="login-card bg-white rounded-2xl border border-slate-200/80 p-8 shadow-xl shadow-slate-200/50">
          <h2
            className="text-[20px] font-medium text-slate-800 mb-1"
            style={{ fontFamily: "'Outfit', sans-serif" }}
          >
            Welcome back
          </h2>
          <p className="text-sm text-slate-400 mb-7">
            Sign in to continue
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-[13px] text-red-500 flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
                {error}
              </div>
            )}

            {/* Username */}
            <div>
              <label
                htmlFor="username"
                className="block text-[13px] font-medium text-slate-500 mb-2 tracking-wide"
              >
                Username
              </label>
              <div
                className={`relative rounded-xl transition-all duration-300 ${
                  focused === "username"
                    ? "ring-2 ring-blue-500/30 shadow-lg shadow-blue-100"
                    : ""
                }`}
              >
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setFocused("username")}
                  onBlur={() => setFocused(null)}
                  className="w-full pl-11 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-[14px] text-slate-700 placeholder-slate-400 focus:outline-none focus:bg-white transition-all duration-300"
                  placeholder="Enter your username"
                  required
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-[13px] font-medium text-slate-500 mb-2 tracking-wide"
              >
                Password
              </label>
              <div
                className={`relative rounded-xl transition-all duration-300 ${
                  focused === "password"
                    ? "ring-2 ring-blue-500/30 shadow-lg shadow-blue-100"
                    : ""
                }`}
              >
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocused("password")}
                  onBlur={() => setFocused(null)}
                  className="w-full pl-11 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-[14px] text-slate-700 placeholder-slate-400 focus:outline-none focus:bg-white transition-all duration-300"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="login-btn w-full py-3 mt-2 bg-blue-600 text-white text-[14px] font-semibold rounded-xl hover:bg-blue-700 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-blue-600/20 hover:shadow-lg hover:shadow-blue-600/25 active:scale-[0.98]"
              style={{ fontFamily: "'Outfit', sans-serif" }}
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                "Sign In"
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-slate-400 mt-8 tracking-wide">
          Secured access &middot; AI Planet
        </p>
      </div>
    </div>
  );
}

export default Login;
