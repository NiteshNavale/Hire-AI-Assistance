
import React from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  BarChart as ReBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip
} from 'recharts';
import { Candidate } from '../types';

interface EvaluationReportProps {
  candidate: Candidate | null;
  onBack: () => void;
}

const EvaluationReport: React.FC<EvaluationReportProps> = ({ candidate, onBack }) => {
  if (!candidate) return null;

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
          <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </button>
        <h2 className="text-2xl font-bold">Candidate Evaluation: {candidate.name}</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Card */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm text-center">
            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${candidate.name}`} className="w-32 h-32 rounded-full mx-auto border-4 border-blue-50 shadow-inner" alt={candidate.name} />
            <h3 className="mt-4 text-xl font-bold">{candidate.name}</h3>
            <p className="text-slate-500 text-sm">{candidate.role}</p>
            
            <div className="mt-8 flex justify-center gap-4">
              <div className="text-center">
                <p className="text-3xl font-black text-blue-600">{candidate.overallScore} / 100</p>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Match Score</p>
              </div>
              <div className="w-px h-12 bg-slate-200"></div>
              <div className="text-center">
                <p className="text-3xl font-black text-green-600">{candidate.technicalScore} / 100</p>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tech Rating</p>
              </div>
            </div>

            <div className="mt-8 space-y-4">
              <button className="w-full py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all">Send Job Offer</button>
              <button className="w-full py-3 bg-slate-50 text-slate-600 rounded-xl font-bold hover:bg-slate-100 transition-all border border-slate-200">Schedule Follow-up</button>
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" /></svg>
              AI Key Insight
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed italic">
              "Highly structured problem solver. Demonstrated exceptional depth in distributed systems during the live technical deep-dive. Communication remains professional but slightly rapid when discussing complex concepts."
            </p>
          </div>
        </div>

        {/* Detailed Metrics */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold mb-8">Competency Matrix</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={candidate.skills}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="name" tick={{fill: '#64748b', fontSize: 12, fontWeight: 500}} />
                    <Radar name={candidate.name} dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.4} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-4">
                {candidate.skills.map((s, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-xs font-bold text-slate-700">
                      <span>{s.name}</span>
                      <span>{s.score} / 100</span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-blue-500 h-full rounded-full" style={{ width: `${s.score}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Skill Gap Analysis */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
              <h3 className="text-lg font-bold">Skill Gap Analysis</h3>
              <div className="space-y-4">
                {candidate.gapAnalysis.map((gap, i) => (
                  <div key={i} className="p-4 bg-orange-50 border border-orange-100 rounded-2xl space-y-1">
                    <div className="flex justify-between items-start">
                      <span className="text-sm font-bold text-orange-800">{gap.skill}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-black uppercase tracking-tighter ${
                        gap.priority === 'High' ? 'bg-red-200 text-red-700' : 
                        gap.priority === 'Medium' ? 'bg-orange-200 text-orange-700' : 
                        'bg-blue-200 text-blue-700'
                      }`}>
                        {gap.priority} Priority
                      </span>
                    </div>
                    <p className="text-xs text-orange-700 leading-relaxed">{gap.gap}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Personalized Training */}
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
              <h3 className="text-lg font-bold">Recommended Training</h3>
              <div className="space-y-4">
                {candidate.trainingPath.map((path, i) => (
                  <div key={i} className="flex gap-4 items-center group cursor-pointer p-2 hover:bg-slate-50 rounded-xl transition-colors">
                    <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center font-bold">
                      {path.type === 'Certification' ? '★' : '▶'}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors">{path.title}</p>
                      <div className="flex gap-2 text-[10px] font-medium text-slate-400">
                        <span>{path.provider}</span>
                        <span>•</span>
                        <span>{path.duration}</span>
                      </div>
                    </div>
                  </div>
                ))}
                <button className="w-full text-xs font-bold text-blue-600 pt-4 border-t border-slate-100 hover:text-blue-800">
                  GENERATE COMPLETE LEARNING PATH →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationReport;
