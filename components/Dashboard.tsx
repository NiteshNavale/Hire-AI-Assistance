
import React, { useState } from 'react';
import { Candidate } from '../types';
import ScheduleModal from './ScheduleModal';

interface DashboardProps {
  candidates: Candidate[];
  onViewCandidate: (id: string) => void;
  onStartInterview: (id: string) => void;
  onStartScreening: () => void;
  onUpdateCandidate: (id: string, updates: Partial<Candidate>) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  candidates, 
  onViewCandidate, 
  onStartInterview,
  onStartScreening,
  onUpdateCandidate
}) => {
  const [selectedForSchedule, setSelectedForSchedule] = useState<Candidate | null>(null);
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null);
  const [toast, setToast] = useState<{msg: string, type: 'success', key?: string} | null>(null);

  const realCandidates = candidates.filter(c => c.id !== 'practice-user');

  const stats = [
    { label: 'Active Pipeline', value: realCandidates.length.toString() },
    { label: 'Scheduled Interviews', value: realCandidates.filter(c => c.status === 'Interviewing').length.toString() },
    { label: 'Avg Match Score', value: realCandidates.length > 0 
        ? (realCandidates.reduce((acc, c) => acc + c.overallScore, 0) / realCandidates.length).toFixed(0) + ' / 100' 
        : '0 / 100' 
    }
  ];

  const handleScheduleConfirm = (id: string, date: string, time: string) => {
    const candidate = candidates.find(c => c.id === id);
    onUpdateCandidate(id, { 
      status: 'Interviewing', 
      interviewDate: date, 
      interviewTime: time 
    });
    setSelectedForSchedule(null);
    setToast({ 
      msg: `Interview scheduled for ${date} at ${time}.`, 
      type: 'success',
      key: candidate?.accessKey
    });
    setTimeout(() => setToast(null), 6000);
  };

  return (
    <div className="space-y-8 animate-fadeIn relative pb-20">
      {toast && (
        <div className="fixed bottom-8 right-8 z-[100] bg-slate-900 text-white px-8 py-6 rounded-3xl shadow-2xl animate-slideUp flex flex-col gap-2 border border-slate-800">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center font-bold">✓</div>
            <p className="font-bold text-sm">{toast.msg}</p>
          </div>
          {toast.key && (
            <div className="mt-2 p-3 bg-white/10 rounded-xl border border-white/10">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Access Key Shared:</p>
              <p className="text-xl font-black text-blue-400 tracking-tighter">{toast.key}</p>
            </div>
          )}
        </div>
      )}

      {selectedForSchedule && (
        <ScheduleModal 
          candidate={selectedForSchedule} 
          onClose={() => setSelectedForSchedule(null)}
          onSchedule={handleScheduleConfirm}
        />
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Recruitment Dashboard</h2>
          <p className="text-slate-500 font-medium tracking-tight italic">AI-analyzed candidate database with secure access key management.</p>
        </div>
        <div className="flex gap-3">
           <div className="bg-emerald-50 text-emerald-700 px-4 py-2 rounded-xl text-xs font-black uppercase flex items-center gap-2 border border-emerald-100">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
            Database Active
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {stats.map((s, i) => (
          <div key={i} className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm transition-all hover:shadow-md">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{s.label}</p>
            <p className="text-3xl font-black text-slate-900">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <h3 className="font-black text-slate-800 uppercase text-xs tracking-widest">Candidate Pipeline</h3>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{realCandidates.length} Active Profiles</span>
        </div>
        
        {realCandidates.length === 0 ? (
          <div className="py-32 text-center space-y-4">
            <div className="w-16 h-16 bg-slate-100 text-slate-300 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 font-bold">👤</div>
            <p className="text-slate-400 font-bold text-lg">Your candidate pool is empty.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/80 text-slate-500 text-[10px] font-black uppercase tracking-wider">
                  <th className="px-8 py-5">Candidate Details</th>
                  <th className="px-8 py-5">Target Role</th>
                  <th className="px-8 py-5">Pipeline Status</th>
                  <th className="px-8 py-5">AI Confidence</th>
                  <th className="px-8 py-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {realCandidates.map((c) => (
                  <React.Fragment key={c.id}>
                    <tr className="hover:bg-blue-50/30 transition-colors group">
                      <td className="px-8 py-6">
                        <div className="flex items-center gap-4">
                          <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${c.name}`} className="w-12 h-12 rounded-2xl border bg-white" alt="" />
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-black text-slate-900">{c.name}</p>
                              {c.isDuplicate && (
                                <span className="px-1.5 py-0.5 bg-red-100 text-red-600 text-[8px] font-black uppercase tracking-widest rounded">DUPLICATE</span>
                              )}
                            </div>
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{c.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <p className="text-sm font-bold text-slate-700">{c.role}</p>
                        {c.interviewDate && (
                          <p className="text-[10px] font-black text-blue-600 uppercase mt-1 bg-blue-50 inline-block px-1.5 py-0.5 rounded tracking-tighter">Round: {c.interviewDate}</p>
                        )}
                      </td>
                      <td className="px-8 py-6">
                        <span className={`inline-flex px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest ${
                          c.status === 'Interviewing' ? 'bg-blue-600 text-white shadow-lg shadow-blue-100' : 'bg-slate-100 text-slate-600'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-8 py-6">
                        <button 
                          onClick={() => setExpandedCandidate(expandedCandidate === c.id ? null : c.id)}
                          className="flex items-center gap-3 bg-white border border-slate-200 px-4 py-2 rounded-2xl hover:border-blue-500 transition-all shadow-sm group/btn"
                        >
                          <span className={`text-sm font-black ${c.overallScore > 80 ? 'text-green-600' : 'text-blue-600'}`}>{c.overallScore} / 100</span>
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest border-l pl-3 group-hover/btn:text-blue-600">Details</span>
                        </button>
                      </td>
                      <td className="px-8 py-6 text-right space-x-2">
                        {c.status === 'Screening' ? (
                          <button 
                            onClick={() => setSelectedForSchedule(c)}
                            className="text-[10px] font-black bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 shadow-xl shadow-blue-50 transition-all active:scale-95 uppercase tracking-widest"
                          >
                            Schedule
                          </button>
                        ) : (
                          <button 
                            onClick={() => onStartInterview(c.id)}
                            className="text-[10px] font-black bg-emerald-600 text-white px-5 py-2.5 rounded-xl hover:bg-emerald-700 shadow-xl shadow-emerald-50 transition-all active:scale-95 uppercase tracking-widest"
                          >
                            Review
                          </button>
                        )}
                      </td>
                    </tr>
                    {expandedCandidate === c.id && (
                      <tr>
                        <td colSpan={5} className="bg-slate-50/50 p-0 overflow-hidden">
                          <div className="p-8 border-b border-slate-200 animate-slideDown">
                            <div className="flex gap-6 mb-8">
                               <div className="flex-1 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm relative overflow-hidden">
                                  <div className="absolute top-0 right-0 p-3 bg-indigo-50 text-indigo-600 text-[10px] font-black uppercase tracking-widest">Security Token</div>
                                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Unique Access Key</p>
                                  <p className="text-3xl font-black text-slate-900 tracking-tighter">{c.accessKey || "KEY-NOT-GEN"}</p>
                                  <p className="text-[10px] text-indigo-500 font-bold mt-2 italic">Sent to candidate with invite for proctored round login.</p>
                               </div>
                               <div className="flex-[2] bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                                  <span className="text-blue-600 font-black uppercase text-[10px] block mb-2">AI Resume Summary</span>
                                  <p className="text-sm font-medium text-slate-700 leading-relaxed">{c.resumeSummary}</p>
                               </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div className="space-y-3">
                                <div className="flex justify-between items-center px-1">
                                  <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Technical Fit</span>
                                  <span className="text-xs font-black text-blue-600">{c.technicalScore}%</span>
                                </div>
                                <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm min-h-[160px]">
                                  <p className="text-xs text-slate-500 leading-relaxed font-medium">{c.technicalReasoning || "Loading technical insights..."}</p>
                                </div>
                              </div>
                              <div className="space-y-3">
                                <div className="flex justify-between items-center px-1">
                                  <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Communication</span>
                                  <span className="text-xs font-black text-blue-600">{c.communicationScore}%</span>
                                </div>
                                <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm min-h-[160px]">
                                  <p className="text-xs text-slate-500 leading-relaxed font-medium">{c.communicationReasoning || "Loading soft skill insights..."}</p>
                                </div>
                              </div>
                              <div className="space-y-3">
                                <div className="flex justify-between items-center px-1">
                                  <span className="text-[10px] font-black text-slate-900 uppercase tracking-widest">Problem Solving</span>
                                  <span className="text-xs font-black text-blue-600">{c.problemSolvingScore}%</span>
                                </div>
                                <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm min-h-[160px]">
                                  <p className="text-xs text-slate-500 leading-relaxed font-medium">{c.problemSolvingReasoning || "Loading analytical insights..."}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
