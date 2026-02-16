
import React, { useState } from 'react';
import { Candidate } from '../types';

interface ScheduleModalProps {
  candidate: Candidate;
  onClose: () => void;
  onSchedule: (id: string, date: string, time: string) => void;
}

const ScheduleModal: React.FC<ScheduleModalProps> = ({ candidate, onClose, onSchedule }) => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden animate-slideUp">
        <div className="p-8 bg-blue-600 text-white text-center">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">
            📅
          </div>
          <h3 className="text-xl font-black">Schedule Interview</h3>
          <p className="text-blue-100 text-sm mt-1">Shortlisting {candidate.name}</p>
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
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Select Time</label>
              <input 
                type="time"
                value={time}
                onChange={e => setTime(e.target.value)}
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
          </div>

          <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100">
            <p className="text-xs text-blue-700 leading-relaxed font-medium">
              Note: Scheduling will trigger an automated email to <strong>{candidate.email}</strong> with calendar invite and meeting link.
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
              onClick={() => onSchedule(candidate.id, date, time)}
              className="flex-2 bg-blue-600 disabled:bg-slate-300 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-blue-100"
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
