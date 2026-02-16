
import React, { useState } from 'react';
import { screenResume } from '../services/geminiService';
import { Candidate } from '../types';

interface CandidatePortalProps {
  onApply: (candidate: Candidate) => void;
  existingCandidates: Candidate[];
}

const generateResumeFingerprint = (text: string): string => {
  const normalized = text.trim().toLowerCase().replace(/\s+/g, '');
  let hash = 0;
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return `v1_${Math.abs(hash)}_${normalized.length}_${normalized.substring(0, 10)}_${normalized.slice(-10)}`;
};

const generateAccessKey = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const part = () => Array.from({length: 4}, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  return `${part()}-${part()}`;
};

const CandidatePortal: React.FC<CandidatePortalProps> = ({ onApply, existingCandidates }) => {
  const [formData, setFormData] = useState({ name: '', email: '', role: '' });
  const [file, setFile] = useState<File | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedKey, setSubmittedKey] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      try {
        const text = await selectedFile.text();
        setFileContent(text);
      } catch (err) {
        console.error("Could not read file text", err);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !formData.name || !formData.email || !formData.role) return;

    setIsSubmitting(true);
    try {
      const resumeText = fileContent || `Resume of ${formData.name}. Applied for ${formData.role}.`;
      const currentFingerprint = generateResumeFingerprint(resumeText);
      const accessKey = generateAccessKey();
      
      const duplicateMatch = existingCandidates.find(c => c.resumeHash === currentFingerprint);
      const jobDesc = `Role: ${formData.role}. Requirements: Deep technical expertise, strong communication, and proven problem-solving skills.`;
      const analysis = await screenResume(resumeText, jobDesc);

      const newCandidate: Candidate = {
        id: Math.random().toString(36).substr(2, 9),
        name: formData.name,
        email: formData.email,
        role: formData.role,
        status: 'Screening',
        accessKey: accessKey,
        overallScore: analysis.overallScore,
        technicalScore: analysis.technicalScore || 0,
        communicationScore: analysis.communicationScore || 0,
        problemSolvingScore: analysis.problemSolvingScore || 0,
        technicalReasoning: analysis.technicalReasoning,
        communicationReasoning: analysis.communicationReasoning,
        problemSolvingReasoning: analysis.problemSolvingReasoning,
        resumeSummary: analysis.summary,
        resumeHash: currentFingerprint,
        isDuplicate: !!duplicateMatch,
        duplicateOf: duplicateMatch ? duplicateMatch.name : undefined,
        points: 0,
        badges: [],
        skills: [
          { name: 'Technical', score: analysis.technicalScore || 0, max: 100 },
          { name: 'Communication', score: analysis.communicationScore || 0, max: 100 },
          { name: 'Problem Solving', score: analysis.problemSolvingScore || 0, max: 100 }
        ],
        gapAnalysis: [],
        trainingPath: []
      };

      onApply(newCandidate);
      setSubmittedKey(accessKey);
    } catch (error) {
      console.error("Application failed", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submittedKey) {
    return (
      <div className="max-w-2xl mx-auto py-20 text-center space-y-8 animate-fadeIn">
        <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-4xl mx-auto shadow-lg">
          ✓
        </div>
        <div className="space-y-4">
          <h2 className="text-3xl font-black text-slate-900">Application Received!</h2>
          <p className="text-slate-500 text-lg">Your screening is complete. Below is your unique interview access key.</p>
        </div>
        
        <div className="bg-white p-8 rounded-3xl border-2 border-dashed border-blue-200 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 left-0 bg-blue-600 text-white px-4 py-1 text-[10px] font-black uppercase tracking-widest">Your Private Key</div>
          <p className="text-5xl font-black text-blue-600 tracking-tighter py-4">{submittedKey}</p>
          <p className="text-xs text-slate-400 font-bold uppercase">Save this key. You will need it to enter the proctored interview room.</p>
        </div>

        <p className="text-slate-500 text-sm italic">An automated email with your interview date and key has been sent to {formData.email}.</p>
        
        <button 
          onClick={() => setSubmittedKey(null)}
          className="text-blue-600 font-black hover:underline uppercase text-xs tracking-widest"
        >
          Return to Portal
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-12 animate-fadeIn">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="space-y-6">
          <h2 className="text-5xl font-black text-slate-900 leading-tight">Apply with <span className="text-blue-600">HireAI</span></h2>
          <p className="text-slate-500 text-lg">Our system generates a unique security key for every applicant to access the proctored AI round.</p>
          <div className="p-6 bg-blue-50 rounded-2xl border border-blue-100">
            <h4 className="font-bold text-blue-800 text-sm mb-2">Proctored AI Round:</h4>
            <p className="text-xs text-blue-700 leading-relaxed">
              If shortlisted, you will use your Access Key to enter a 30-minute high-security interview session involving camera, microphone, and screen share.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xl space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Full Name</label>
              <input type="text" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Work Email</label>
              <input type="email" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Target Role</label>
              <select required value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})} className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select Role</option>
                <option value="Software Engineer">Software Engineer</option>
                <option value="Data Analyst">Data Analyst</option>
                <option value="Product Manager">Product Manager</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Resume Content</label>
              <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-blue-400 cursor-pointer relative">
                <input type="file" required onChange={handleFileChange} className="absolute inset-0 opacity-0 cursor-pointer" />
                <p className="text-slate-500 font-bold">{file ? file.name : "Drop Resume Here"}</p>
                <p className="text-[10px] text-slate-400 mt-2">Analysis is deterministic and plagiarism-checked.</p>
              </div>
            </div>
          </div>
          <button disabled={isSubmitting} className="w-full py-4 rounded-xl font-black text-white bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 shadow-lg shadow-blue-100 transition-all active:scale-95">
            {isSubmitting ? "GENERATING ACCESS KEY..." : "APPLY & SCREEN"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CandidatePortal;
