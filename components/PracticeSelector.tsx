
import React, { useState } from 'react';

interface PracticeSelectorProps {
  onStart: (role: string) => void;
}

const PracticeSelector: React.FC<PracticeSelectorProps> = ({ onStart }) => {
  const [role, setRole] = useState('');
  const popularRoles = [
    'Software Engineer',
    'Data Scientist',
    'Product Manager',
    'UX Designer',
    'Sales Representative',
    'Financial Analyst'
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-12 py-12 animate-fadeIn">
      <div className="text-center space-y-4">
        <div className="w-20 h-20 bg-blue-100 text-blue-600 rounded-3xl flex items-center justify-center text-4xl mx-auto mb-6 shadow-xl shadow-blue-50 border border-blue-200">
          🎯
        </div>
        <h2 className="text-4xl font-black text-slate-900">Mock Interviewer Mode</h2>
        <p className="text-slate-500 text-lg max-w-lg mx-auto">
          Select a role to start a gamified practice session. Get real-time AI coaching and earn points to climb the leaderboard.
        </p>
      </div>

      <div className="bg-white p-10 rounded-3xl border border-slate-200 shadow-xl shadow-slate-100 space-y-10">
        <div className="space-y-4">
          <label className="block text-sm font-black text-slate-700 uppercase tracking-widest">Select your Target Role</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {popularRoles.map((r) => (
              <button
                key={r}
                onClick={() => setRole(r)}
                className={`p-4 rounded-2xl border-2 transition-all font-bold text-sm ${
                  role === r 
                  ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-inner' 
                  : 'border-slate-100 bg-slate-50 text-slate-500 hover:border-slate-200'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <label className="block text-sm font-black text-slate-700 uppercase tracking-widest">Or Type a custom Role</label>
          <input 
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g. Lead Devops Engineer..."
            className="w-full p-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all font-medium"
          />
        </div>

        <button
          disabled={!role}
          onClick={() => onStart(role)}
          className={`w-full py-5 rounded-2xl font-black text-lg transition-all shadow-xl ${
            !role 
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
            : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-200 active:scale-95'
          }`}
        >
          START PRACTICE SESSION
        </button>

        <div className="grid grid-cols-3 gap-6 pt-4 text-center border-t border-slate-100">
          <div>
            <p className="text-2xl mb-1">💬</p>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Real-time Feedback</p>
          </div>
          <div>
            <p className="text-2xl mb-1">🏆</p>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Earn Points</p>
          </div>
          <div>
            <p className="text-2xl mb-1">🚀</p>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Skill Leveling</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PracticeSelector;
