
import React, { useState } from 'react';
import { Candidate } from '../types';

interface CandidateInterviewAccessProps {
  candidates: Candidate[];
  onLogin: (candidate: Candidate) => void;
}

const CandidateInterviewAccess: React.FC<CandidateInterviewAccessProps> = ({ candidates, onLogin }) => {
  const [accessKey, setAccessKey] = useState('');
  const [error, setError] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [countdownMsg, setCountdownMsg] = useState<string | null>(null);

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    setError('');
    setCountdownMsg(null);

    setTimeout(() => {
      const candidate = candidates.find(c => c.accessKey?.toUpperCase() === accessKey.trim().toUpperCase());
      
      if (candidate) {
        // Special case: If round 2 is scheduled or offer stage, let them in regardless of aptitude time
        if (['Interview Scheduled', 'VP Approval', 'Offer Signed', 'Offer Sent', 'Offer Accepted', 'Offer Expired'].includes(candidate.status)) {
            onLogin(candidate);
            return;
        }

        // Check if Aptitude Date is set
        if (!candidate.aptitudeDate || !candidate.aptitudeTime) {
             setError("Your exam has not been scheduled by HR yet.");
             setIsVerifying(false);
             return;
        }

        const now = new Date();
        const scheduledTime = new Date(`${candidate.aptitudeDate}T${candidate.aptitudeTime}`);
        
        // Simple comparison
        if (now < scheduledTime) {
            const diffMs = scheduledTime.getTime() - now.getTime();
            const diffMins = Math.ceil(diffMs / (1000 * 60));
            const diffHours = Math.floor(diffMins / 60);
            
            setCountdownMsg(`Exam Locked. Starts in ${diffHours}h ${diffMins % 60}m.`);
            setIsVerifying(false);
            return;
        }

        onLogin(candidate);
      } else {
        setError('Invalid access key. Please check your email or contact the recruiter.');
        setIsVerifying(false);
      }
    }, 1200);
  };

  return (
    <div className="max-w-md mx-auto mt-16 animate-fadeIn">
      <div className="bg-white p-10 rounded-3xl border border-slate-200 shadow-2xl space-y-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full -translate-y-1/2 translate-x-1/2 opacity-50"></div>
        
        <div className="text-center space-y-3">
          <div className="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center text-2xl mx-auto shadow-xl shadow-blue-100">
            🔐
          </div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Candidate Portal</h2>
          <p className="text-slate-500 text-sm font-medium">Enter your key to access Exams or Interviews.</p>
        </div>

        <form onSubmit={handleVerify} className="space-y-6">
          <div className="space-y-2">
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest">Access Key</label>
            <input 
              type="text" 
              required
              placeholder="XXXX-XXXX"
              value={accessKey}
              onChange={e => setAccessKey(e.target.value.toUpperCase())}
              className="w-full p-4 bg-slate-50 border-2 border-slate-100 rounded-2xl text-center text-2xl font-black tracking-widest outline-none focus:ring-4 focus:ring-blue-50 focus:border-blue-500 transition-all uppercase"
            />
          </div>

          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold border border-red-100 flex items-center gap-3 animate-slideUp">
              <span className="text-lg">⚠️</span>
              {error}
            </div>
          )}

          {countdownMsg && (
            <div className="p-6 bg-amber-50 text-amber-700 rounded-2xl text-center border border-amber-100 animate-slideUp">
                <p className="text-2xl font-bold mb-2">⏳</p>
                <p className="font-black text-lg">{countdownMsg}</p>
                <p className="text-xs mt-2 opacity-80">Please return at the scheduled time.</p>
            </div>
          )}

          {!countdownMsg && (
            <button 
                disabled={isVerifying || accessKey.length < 5}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white rounded-2xl font-black transition-all shadow-xl shadow-blue-100 active:scale-95 flex items-center justify-center gap-3"
            >
                {isVerifying ? (
                <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    VERIFYING...
                </>
                ) : "AUTHENTICATE"}
            </button>
          )}
        </form>
      </div>

      <div className="mt-8 text-center">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">System Security Level: High</p>
      </div>
    </div>
  );
};

export default CandidateInterviewAccess;
