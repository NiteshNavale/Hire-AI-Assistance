
import React, { useState } from 'react';

interface LoginProps {
  onLoginSuccess: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // --- SECURE LOGIN CODE (COMMENTED OUT FOR LATER) ---
    /*
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); 

      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        signal: controller.signal
      }).catch(() => null); 

      clearTimeout(timeoutId);

      if (response && response.ok) {
        const data = await response.json();
        onLoginSuccess(data.token);
        return;
      }
    } catch (err) {
      console.error("Backend login failed", err);
    }
    */
    // --- END SECURE LOGIN CODE ---

    // Simple Immediate Local Auth for AI Studio
    setTimeout(() => {
      if (username === 'admin' && password === 'admin123') {
        const mockToken = 'local-session-' + Math.random().toString(36).substr(2);
        onLoginSuccess(mockToken);
      } else {
        setError('Invalid username or password.');
        setIsLoading(false);
      }
    }, 500); // Small delay for UX feel
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-8 bg-white rounded-3xl border border-slate-200 shadow-2xl animate-slideUp">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white text-2xl font-black mx-auto mb-4">
          H
        </div>
        <h2 className="text-2xl font-black text-slate-900">HR Portal Login</h2>
        <p className="text-slate-500 text-sm mt-1">Authorized Access Only</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Username</label>
          <input
            type="text"
            required
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 font-medium"
            placeholder="admin"
          />
        </div>
        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Password</label>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 font-medium"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 text-red-600 text-xs font-bold rounded-xl border border-red-100 animate-fadeIn flex items-center gap-2">
            <span>⚠</span> {error}
          </div>
        )}

        <button
          disabled={isLoading}
          type="submit"
          className={`w-full py-4 font-black rounded-xl transition-all active:scale-95 shadow-lg flex items-center justify-center gap-3 ${
            isLoading 
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-100'
          }`}
        >
          {isLoading && (
            <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
          )}
          {isLoading ? 'BYPASSING TO DASHBOARD...' : 'SECURE LOGIN'}
        </button>
      </form>

      <div className="mt-8 pt-8 border-t border-slate-100 text-center">
        <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest leading-relaxed">
          Quick Access (AI Studio): <strong>admin</strong> / <strong>admin123</strong>
        </p>
      </div>
    </div>
  );
};

export default Login;
