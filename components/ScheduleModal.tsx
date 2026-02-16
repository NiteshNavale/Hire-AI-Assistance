
import React, { useState } from 'react';
import { Candidate } from '../types';

interface ScheduleModalProps {
  candidate: Candidate;
  type: 'aptitude' | 'interview';
  onClose: () => void;
  onSchedule: (id: string, date: string, time: string, type: 'aptitude' | 'interview') => void;
}

const ScheduleModal: React.FC<ScheduleModalProps> = ({ candidate, type, onClose, onSchedule }) => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden animate-slideUp">
        <div className={`p-8 text-white text-center ${type === 'aptitude' ? 'bg-blue-600' : 'bg-purple-600'}`}>
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">
            {type === 'aptitude' ? '📝' : '🤝'}
          </div>
          <h3 className="text-xl font-black">{type === 'aptitude' ? 'Schedule Aptitude Exam' : 'Schedule Final Interview'}</h3>
          <p className="text-white/80 text-sm mt-1">Candidate: {candidate.name}</p>
        </div>

        <div className="p-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Select Date</label>
              <input 
                type="date"
                value={date}
                onChange={e => setDate(e.target.value)}
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Start Time</label>
              <input 
                type="time"
                value={time}
                onChange={e => setTime(e.target.value)}
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>

          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
            <p className="text-xs text-slate-600 leading-relaxed font-medium">
              Note: Automated email will be sent to <strong>{candidate.email}</strong> with {type === 'aptitude' ? 'exam access instructions' : 'meeting link'}.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <button 
              onClick={onClose}
              className="flex-1 py-3 text-sm font-bold text-slate-500 hover:bg-slate-50 rounded-xl transition-all"
            >
              Cancel
            </button>
            <button 
              disabled={!date || !time}
              onClick={() => onSchedule(candidate.id, date, time, type)}
              className={`flex-2 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg active:scale-95 disabled:bg-slate-300 ${
                  type === 'aptitude' ? 'bg-blue-600 hover:bg-blue-700 shadow-blue-100' : 'bg-purple-600 hover:bg-purple-700 shadow-purple-100'
              }`}
            >
              Confirm & Notify
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScheduleModal;
