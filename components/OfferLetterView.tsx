import React, { useState, useEffect } from 'react';
import { Candidate } from '../types';

interface OfferLetterViewProps {
  candidate: Candidate;
  onAccept: () => void;
  onLogout: () => void;
}

const OfferLetterView: React.FC<OfferLetterViewProps> = ({ candidate, onAccept, onLogout }) => {
  const [timeLeft, setTimeLeft] = useState<string>('');
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    if (!candidate.offerLetter?.expiryDate) return;

    const interval = setInterval(() => {
      const now = new Date().getTime();
      const expiry = new Date(candidate.offerLetter!.expiryDate).getTime();
      const distance = expiry - now;

      if (distance < 0) {
        clearInterval(interval);
        setIsExpired(true);
        setTimeLeft("EXPIRED");
      } else {
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        setTimeLeft(`${days}d ${hours}h ${minutes}m`);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [candidate.offerLetter]);

  if (!candidate.offerLetter) return null;

  return (
    <div className="max-w-3xl mx-auto py-12 animate-fadeIn">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl overflow-hidden relative">
        {/* Header */}
        <div className="bg-slate-900 text-white p-8 text-center relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full bg-blue-600 opacity-10"></div>
            <div className="relative z-10">
                <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4 backdrop-blur-sm">
                    📜
                </div>
                <h1 className="text-3xl font-black tracking-tight mb-2">Official Job Offer</h1>
                <p className="text-blue-200 font-medium">HireAI Recruitment Team</p>
            </div>
        </div>

        {/* Body */}
        <div className="p-10 space-y-8">
            <div className="flex justify-between items-start border-b border-slate-100 pb-8">
                <div>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Prepared For</p>
                    <p className="text-xl font-black text-slate-900">{candidate.name}</p>
                    <p className="text-sm font-bold text-slate-500">{candidate.role}</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Offer Valid Until</p>
                    <p className={`text-xl font-black ${isExpired ? 'text-red-500' : 'text-blue-600'}`}>
                        {timeLeft}
                    </p>
                </div>
            </div>

            <div className="prose prose-slate max-w-none">
                <p>Dear {candidate.name},</p>
                <p>
                    We are pleased to offer you the position of <strong>{candidate.role}</strong> at HireAI. 
                    Your impressive performance in our evaluation process has convinced us that you will be a valuable asset to our team.
                </p>
                <p>
                    This offer is contingent upon your acceptance within the validity period shown above.
                </p>
                <p>
                    <strong>Notice Period:</strong> {candidate.noticePeriod}<br/>
                    <strong>Signed By:</strong> {candidate.offerLetter.signedBy}<br/>
                    <strong>Date:</strong> {new Date(candidate.offerLetter.dateSigned).toLocaleDateString()}
                </p>
            </div>

            {/* Actions */}
            <div className="pt-8 border-t border-slate-100 flex flex-col gap-4">
                {candidate.status === 'Offer Accepted' ? (
                    <div className="bg-green-50 text-green-700 p-6 rounded-2xl text-center border border-green-100">
                        <p className="text-2xl mb-2">🎉</p>
                        <p className="font-black text-xl">Offer Accepted!</p>
                        <p className="text-sm">Welcome to the team. HR will contact you shortly for onboarding.</p>
                    </div>
                ) : isExpired ? (
                    <div className="bg-red-50 text-red-700 p-6 rounded-2xl text-center border border-red-100">
                        <p className="font-black text-xl">Offer Expired</p>
                        <p className="text-sm">This offer is no longer valid. Please contact HR.</p>
                    </div>
                ) : (
                    <div className="flex gap-4">
                        <button className="flex-1 py-4 rounded-xl font-bold text-slate-500 hover:bg-slate-50 border border-slate-200 transition-colors uppercase tracking-widest text-xs">
                            Decline
                        </button>
                        <button 
                            onClick={onAccept}
                            className="flex-[2] py-4 rounded-xl font-black text-white bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all active:scale-95 uppercase tracking-widest text-xs"
                        >
                            Accept Offer
                        </button>
                    </div>
                )}
            </div>
        </div>
        
        <div className="bg-slate-50 p-4 text-center">
            <button onClick={onLogout} className="text-xs font-bold text-slate-400 hover:text-slate-600 uppercase tracking-widest">
                Log Out
            </button>
        </div>
      </div>
    </div>
  );
};

export default OfferLetterView;
