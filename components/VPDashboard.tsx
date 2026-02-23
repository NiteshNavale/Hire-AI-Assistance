import React, { useState } from 'react';
import { Candidate } from '../types';

interface VPDashboardProps {
  candidates: Candidate[];
  onUpdateCandidate: (id: string, updates: Partial<Candidate>) => void;
  onLogout: () => void;
}

const VPDashboard: React.FC<VPDashboardProps> = ({ candidates, onUpdateCandidate, onLogout }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filter for candidates pending VP approval
  // Sort by overall score descending to show "Top 5"
  const pendingCandidates = candidates
    .filter(c => c.status === 'VP Approval')
    .sort((a, b) => b.overallScore - a.overallScore);

  const topCandidates = pendingCandidates.slice(0, 5);
  const otherCandidates = pendingCandidates.slice(5);

  const handleSignOffer = (candidate: Candidate) => {
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + 3); // 3 days validity

    onUpdateCandidate(candidate.id, {
      status: 'Offer Signed',
      offerLetter: {
        signedBy: 'Vice President',
        dateSigned: new Date().toISOString(),
        expiryDate: expiryDate.toISOString(),
      }
    });
    setExpandedId(null);
  };

  const renderCandidateCard = (c: Candidate, isTop: boolean) => (
    <div key={c.id} className={`bg-white rounded-3xl border ${isTop ? 'border-blue-200 shadow-lg' : 'border-slate-200 shadow-sm'} overflow-hidden transition-all`}>
      <div className="p-6 flex items-center justify-between cursor-pointer" onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}>
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-xl ${isTop ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
            {c.overallScore}
          </div>
          <div>
            <h3 className="font-black text-slate-900">{c.name}</h3>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">{c.role}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
            <div className="text-right">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Notice Period</p>
                <p className="font-bold text-slate-800">{c.noticePeriod || 'N/A'}</p>
            </div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-transform ${expandedId === c.id ? 'rotate-180' : ''}`}>
                ▼
            </div>
        </div>
      </div>
      
      {expandedId === c.id && (
        <div className="px-6 pb-6 pt-0 animate-fadeIn">
            <div className="h-px bg-slate-100 mb-6"></div>
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Technical</p>
                    <p className="text-xl font-black text-slate-900">{c.technicalScore}%</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Communication</p>
                    <p className="text-xl font-black text-slate-900">{c.communicationScore}%</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-2xl">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Problem Solving</p>
                    <p className="text-xl font-black text-slate-900">{c.problemSolvingScore}%</p>
                </div>
            </div>
            
            <div className="mb-6">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Resume Summary</p>
                <p className="text-sm text-slate-600 leading-relaxed">{c.resumeSummary}</p>
            </div>

            <div className="flex justify-end gap-3">
                <button className="px-6 py-3 rounded-xl font-bold text-slate-500 hover:bg-slate-100 transition-colors">
                    Reject
                </button>
                <button 
                    onClick={(e) => { e.stopPropagation(); handleSignOffer(c); }}
                    className="px-6 py-3 rounded-xl font-black text-white bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-100 transition-all active:scale-95 flex items-center gap-2"
                >
                    <span>✍️</span> SIGN OFFER LETTER
                </button>
            </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-8 animate-fadeIn pb-20">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Executive Approval</h2>
          <p className="text-slate-500 font-medium tracking-tight italic">Review top candidates and sign offer letters.</p>
        </div>
        <button onClick={onLogout} className="text-xs font-black text-red-500 bg-red-50 px-4 py-2 rounded-lg hover:bg-red-100 transition-colors uppercase tracking-widest">
            Logout VP
        </button>
      </div>

      {pendingCandidates.length === 0 ? (
        <div className="py-32 text-center space-y-4 bg-white rounded-3xl border border-slate-200">
            <div className="w-16 h-16 bg-slate-100 text-slate-300 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 font-bold">✓</div>
            <p className="text-slate-400 font-bold text-lg">All caught up! No pending approvals.</p>
        </div>
      ) : (
        <div className="space-y-8">
            <div>
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-xs font-black text-blue-600 bg-blue-50 px-2 py-1 rounded uppercase tracking-widest">Priority</span>
                    <h3 className="font-black text-slate-900 uppercase tracking-widest text-sm">Top 5 Candidates</h3>
                </div>
                <div className="space-y-4">
                    {topCandidates.map(c => renderCandidateCard(c, true))}
                </div>
            </div>

            {otherCandidates.length > 0 && (
                <div>
                    <h3 className="font-black text-slate-400 uppercase tracking-widest text-sm mb-4">Other Candidates</h3>
                    <div className="space-y-4">
                        {otherCandidates.map(c => renderCandidateCard(c, false))}
                    </div>
                </div>
            )}
        </div>
      )}
    </div>
  );
};

export default VPDashboard;
