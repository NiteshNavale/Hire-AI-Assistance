
import React from 'react';
import { Candidate, BADGES } from '../types';

interface LeaderboardProps {
  candidates: Candidate[];
}

const Leaderboard: React.FC<LeaderboardProps> = ({ candidates }) => {
  // Sort by points descending
  const sorted = [...candidates]
    .filter(c => c.id !== 'practice-user')
    .sort((a, b) => b.points - a.points);

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      <div className="flex items-end justify-between gap-4 border-b border-slate-200 pb-8">
        <div>
          <h2 className="text-3xl font-black text-slate-900">Skill Leaderboard</h2>
          <p className="text-slate-500 mt-1">Global rankings based on performance points and skill badges.</p>
        </div>
        <div className="flex gap-2">
          <button className="bg-white border border-slate-200 px-4 py-2 rounded-xl text-sm font-bold shadow-sm">This Week</button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg shadow-blue-100">All Time</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {sorted.slice(0, 3).map((c, i) => (
          <div key={c.id} className={`relative p-8 rounded-3xl border text-center transition-all ${
            i === 0 ? 'bg-gradient-to-b from-amber-50 to-white border-amber-100 shadow-xl shadow-amber-50 md:scale-105 z-10' : 'bg-white border-slate-100 shadow-sm'
          }`}>
            <div className={`absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full flex items-center justify-center font-black text-white ${
              i === 0 ? 'bg-amber-400' : i === 1 ? 'bg-slate-400' : 'bg-orange-400'
            }`}>
              {i + 1}
            </div>
            <img src={`https://picsum.photos/seed/${c.id}/100/100`} className="w-20 h-20 rounded-full mx-auto mb-4 border-4 border-white shadow-md" alt={c.name} />
            <h3 className="text-lg font-black text-slate-900">{c.name}</h3>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-4">{c.role}</p>
            <div className="text-2xl font-black text-blue-600">{c.points.toLocaleString()} <span className="text-[10px] text-slate-400">PTS</span></div>
            <div className="flex justify-center gap-1 mt-4">
              {c.badges.slice(0, 3).map(bId => (
                <span key={bId} className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center text-sm border border-slate-100 shadow-sm" title={BADGES[bId]?.name}>{BADGES[bId]?.icon}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
              <th className="px-8 py-4">Rank</th>
              <th className="px-8 py-4">Candidate</th>
              <th className="px-8 py-4">Points</th>
              <th className="px-8 py-4">Top Badges</th>
              <th className="px-8 py-4 text-right">Trend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {sorted.map((c, i) => (
              <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-8 py-6">
                  <span className={`text-lg font-black ${i < 3 ? 'text-blue-600' : 'text-slate-400'}`}>#{i + 1}</span>
                </td>
                <td className="px-8 py-6">
                  <div className="flex items-center gap-4">
                    <img src={`https://picsum.photos/seed/${c.id}/40/40`} className="w-10 h-10 rounded-xl" alt="" />
                    <div>
                      <p className="text-sm font-black text-slate-800">{c.name}</p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase">{c.role}</p>
                    </div>
                  </div>
                </td>
                <td className="px-8 py-6">
                  <div className="text-sm font-black text-slate-900">{c.points.toLocaleString()}</div>
                </td>
                <td className="px-8 py-6">
                  <div className="flex gap-2">
                    {c.badges.map(bId => (
                      <span key={bId} className="px-2 py-1 bg-slate-50 border border-slate-100 rounded-md text-xs" title={BADGES[bId]?.name}>{BADGES[bId]?.icon}</span>
                    ))}
                  </div>
                </td>
                <td className="px-8 py-6 text-right">
                  <span className="text-xs font-bold text-green-500">▲ {Math.floor(Math.random() * 10) + 1}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Leaderboard;
