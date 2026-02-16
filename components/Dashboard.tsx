
import React, { useState } from 'react';
import { Candidate } from '../types';
import ScheduleModal from './ScheduleModal';
import AddUserModal from './AddUserModal';

interface DashboardProps {
  candidates: Candidate[];
  authToken?: string | null;
  onViewCandidate: (id: string) => void;
  onStartInterview: (id: string) => void;
  onStartScreening: () => void;
  onUpdateCandidate: (id: string, updates: Partial<Candidate>) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  candidates, 
  authToken,
  onViewCandidate, 
  onStartInterview,
  onStartScreening,
  onUpdateCandidate
}) => {
  const [scheduleModalOpen, setScheduleModalOpen] = useState<{candidate: Candidate, type: 'aptitude'|'interview'} | null>(null);
  const [showAddUser, setShowAddUser] = useState(false);
  const [toast, setToast] = useState<{msg: string, type: 'success', key?: string} | null>(null);

  const realCandidates = candidates.filter(c => c.id !== 'practice-user');

  const stats = [
    { label: 'Screening', value: realCandidates.filter(c => c.status === 'Screening').length.toString() },
    { label: 'Aptitude Pending', value: realCandidates.filter(c => c.status === 'Aptitude Scheduled').length.toString() },
    { label: 'Round 2 Set', value: realCandidates.filter(c => c.status === 'Interview Scheduled').length.toString() }
  ];

  const handleScheduleConfirm = (id: string, date: string, time: string, type: 'aptitude'|'interview') => {
    const candidate = candidates.find(c => c.id === id);
    if (!candidate) return;

    if (type === 'aptitude') {
        onUpdateCandidate(id, { 
            status: 'Aptitude Scheduled', 
            aptitudeDate: date, 
            aptitudeTime: time 
        });
        setToast({ msg: `Aptitude Exam scheduled for ${date} at ${time}. Email sent.`, type: 'success' });
    } else {
        const link = `https://meet.google.com/abc-${Math.random().toString(36).substr(2, 4)}-xyz`;
        onUpdateCandidate(id, { 
            status: 'Interview Scheduled', 
            round2Date: date, 
            round2Time: time,
            round2Link: link
        });
        setToast({ msg: `Round 2 Interview scheduled. Meeting link generated.`, type: 'success' });
    }
    
    setScheduleModalOpen(null);
    setTimeout(() => setToast(null), 6000);
  };

  const handleAddUser = async (u: string, p: string) => {
    // Disabled in simplified auth mode
    return false;
  };

  return (
    <div className="space-y-8 animate-fadeIn relative pb-20">
      {toast && (
        <div className="fixed bottom-8 right-8 z-[100] bg-slate-900 text-white px-8 py-6 rounded-3xl shadow-2xl animate-slideUp flex flex-col gap-2 border border-slate-800">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center font-bold">✓</div>
            <p className="font-bold text-sm">{toast.msg}</p>
          </div>
        </div>
      )}

      {showAddUser && (
        <AddUserModal onClose={() => setShowAddUser(false)} onAdd={handleAddUser} />
      )}

      {scheduleModalOpen && (
        <ScheduleModal 
          candidate={scheduleModalOpen.candidate} 
          type={scheduleModalOpen.type}
          onClose={() => setScheduleModalOpen(null)}
          onSchedule={handleScheduleConfirm}
        />
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Recruitment Dashboard</h2>
          <p className="text-slate-500 font-medium tracking-tight italic">Manage Aptitude Exams and Final Interviews.</p>
        </div>
        <div className="flex gap-3">
           {/* Manage Access Button Removed for Simplified Login Mode */}
           <button onClick={onStartScreening} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-blue-100 active:scale-95">
             + New Batch Screening
           </button>
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
                  <th className="px-8 py-5">Candidate</th>
                  <th className="px-8 py-5">Stage</th>
                  <th className="px-8 py-5">Scores (Resume / Aptitude)</th>
                  <th className="px-8 py-5 text-right">Next Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {realCandidates.map((c) => {
                  const isPassed = (c.aptitudeScore || 0) >= 50;
                  
                  return (
                    <React.Fragment key={c.id}>
                      <tr className="hover:bg-blue-50/30 transition-colors group">
                        <td className="px-8 py-6">
                          <div className="flex items-center gap-4">
                            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${c.name}`} className="w-12 h-12 rounded-2xl border bg-white" alt="" />
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-black text-slate-900">{c.name}</p>
                              </div>
                              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{c.role}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-8 py-6">
                          <span className={`inline-flex px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest ${
                            c.status === 'Interview Scheduled' ? 'bg-purple-600 text-white' :
                            c.status === 'Aptitude Completed' ? (isPassed ? 'bg-green-600 text-white' : 'bg-red-100 text-red-600') :
                            c.status === 'Aptitude Scheduled' ? 'bg-orange-100 text-orange-600' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            {c.status === 'Aptitude Completed' && !isPassed ? 'Failed Aptitude' : c.status}
                          </span>
                          {c.aptitudeDate && c.status === 'Aptitude Scheduled' && (
                              <div className="text-[10px] text-slate-400 font-bold mt-1">Due: {c.aptitudeDate} {c.aptitudeTime}</div>
                          )}
                          {c.round2Date && c.status === 'Interview Scheduled' && (
                              <div className="text-[10px] text-purple-400 font-bold mt-1">{c.round2Date} {c.round2Time}</div>
                          )}
                        </td>
                        <td className="px-8 py-6">
                          <div className="flex gap-4">
                              <div>
                                  <span className="text-xs font-bold text-slate-400 block uppercase">Resume</span>
                                  <span className="text-sm font-black text-slate-900">{c.overallScore}%</span>
                              </div>
                              {c.aptitudeScore !== undefined && c.aptitudeScore !== null && (
                                  <div>
                                      <span className="text-xs font-bold text-slate-400 block uppercase">Aptitude</span>
                                      <div className="flex items-center gap-2">
                                        <span className={`text-sm font-black ${isPassed ? 'text-green-600' : 'text-red-600'}`}>
                                          {c.aptitudeScore}%
                                        </span>
                                        <span className={`text-[8px] px-1.5 py-0.5 rounded uppercase font-bold ${isPassed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {isPassed ? 'PASS' : 'FAIL'}
                                        </span>
                                      </div>
                                  </div>
                              )}
                          </div>
                        </td>
                        <td className="px-8 py-6 text-right">
                          {/* Action Logic */}
                          {c.status === 'Screening' && (
                            <button 
                              onClick={() => setScheduleModalOpen({candidate: c, type: 'aptitude'})}
                              className="text-[10px] font-black bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 shadow-xl shadow-blue-50 transition-all active:scale-95 uppercase tracking-widest"
                            >
                              Schedule Aptitude
                            </button>
                          )}
                          
                          {(c.status === 'Aptitude Scheduled') && (
                               <span className="text-[10px] font-bold text-orange-400 italic">Waiting for Exam...</span>
                          )}

                          {(c.status === 'Aptitude Completed') && (
                            isPassed ? (
                              <button 
                                onClick={() => setScheduleModalOpen({candidate: c, type: 'interview'})}
                                className="text-[10px] font-black bg-purple-600 text-white px-5 py-2.5 rounded-xl hover:bg-purple-700 shadow-xl shadow-purple-50 transition-all active:scale-95 uppercase tracking-widest"
                              >
                                Schedule Round 2
                              </button>
                            ) : (
                              <span className="text-[10px] font-black text-slate-400 bg-slate-100 px-3 py-2.5 rounded-xl uppercase tracking-widest">
                                Not Qualified
                              </span>
                            )
                          )}

                          {c.status === 'Interview Scheduled' && c.round2Link && (
                               <a 
                                  href={c.round2Link}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-block text-[10px] font-black bg-emerald-600 text-white px-5 py-2.5 rounded-xl hover:bg-emerald-700 shadow-xl shadow-emerald-50 transition-all active:scale-95 uppercase tracking-widest"
                                >
                                  Join Meeting
                                </a>
                          )}
                        </td>
                      </tr>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
