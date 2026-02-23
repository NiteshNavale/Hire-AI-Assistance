
import React, { useState } from 'react';

interface LoginProps {
  onLoginSuccess: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [role, setRole] = useState<'HR' | 'VP'>('HR');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // ---------------------------------------------------------
    // CLIENT-SIDE AUTHENTICATION (Database Bypass)
    // ---------------------------------------------------------
    if (role === 'HR' && username === 'admin' && password === 'admin123') {
        const token = 'admin-bypass-' + Date.now();
        setTimeout(() => {
            onLoginSuccess(token); // HR Token
        }, 600);
        return;
    }

    if (role === 'VP' && username === 'vp' && password === 'vp123') {
        const token = 'vp-bypass-' + Date.now();
        setTimeout(() => {
            onLoginSuccess(token); // VP Token
        }, 600);
        return;
    }
    // ---------------------------------------------------------

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      // Check content type to avoid parsing HTML (SPA fallback) as JSON
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.indexOf("application/json") === -1) {
        throw new Error("Received non-JSON response from server (likely HTML fallback).");
      }

      if (response.ok) {
        const data = await response.json();
        onLoginSuccess(data.token);
        return; 
      } 
      
      // Handle known API errors
      if (response.status === 401) {
           setError('Invalid username or password.');
      } else {
           setError(`Server Error (${response.status}).`);
      }

    } catch (err: any) {
      clearTimeout(timeoutId);
      console.log("Backend login failed:", err);
      setError(`Invalid ${role} credentials.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-8 bg-white rounded-3xl border border-slate-200 shadow-2xl animate-slideUp">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white text-2xl font-black mx-auto mb-4">
          H
        </div>
        <h2 className="text-2xl font-black text-slate-900">{role} Portal Login</h2>
        <p className="text-slate-500 text-sm mt-1">Authorized Access Only</p>
      </div>

      <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
        <button 
            type="button"
            onClick={() => setRole('HR')} 
            className={`flex-1 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${role === 'HR' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-400'}`}
        >
            HR Admin
        </button>
        <button 
            type="button"
            onClick={() => setRole('VP')} 
            className={`flex-1 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all ${role === 'VP' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-400'}`}
        >
            Vice President
        </button>
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
            placeholder={role === 'HR' ? "admin" : "vp"}
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
          {isLoading ? 'AUTHENTICATING...' : 'SECURE LOGIN'}
        </button>
      </form>

      <div className="mt-8 pt-8 border-t border-slate-100 text-center">
        <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest leading-relaxed">
          {role === 'HR' ? 'Default Admin: admin / admin123' : 'Default VP: vp / vp123'}
        </p>
      </div>
    </div>
  );
};

export default Login;
