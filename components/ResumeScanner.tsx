
import React, { useState } from 'react';
import { screenResume } from '../services/geminiService';
import { Candidate } from '../types';

interface ResumeScannerProps {
  onComplete: () => void;
  existingCandidates: Candidate[];
  onResults: (newCandidates: Candidate[]) => void;
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

const ResumeScanner: React.FC<ResumeScannerProps> = ({ onComplete, existingCandidates, onResults }) => {
  const [jobDescription, setJobDescription] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<any[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const startScanning = async () => {
    if (!jobDescription || files.length === 0) return;
    setIsScanning(true);
    
    const processedResults = [];
    const newCandidatesForState: Candidate[] = [];

    for (const file of files) {
      try {
        const text = await file.text();
        const fingerprint = generateResumeFingerprint(text);
        
        // Internal and External Duplicate Check using Fingerprints
        const duplicateMatch = [...existingCandidates, ...newCandidatesForState].find(c => 
          c.resumeHash === fingerprint
        );

        const analysis = await screenResume(text, jobDescription);
        
        const candidate: Candidate = {
          id: Math.random().toString(36).substr(2, 9),
          name: file.name.split('.')[0],
          email: `${file.name.split('.')[0].toLowerCase()}@batch-import.ai`,
          role: jobDescription.substring(0, 30) + (jobDescription.length > 30 ? "..." : ""),
          status: 'Screening',
          overallScore: analysis.overallScore,
          technicalScore: analysis.technicalScore || 0,
          communicationScore: analysis.communicationScore || 0,
          problemSolvingScore: analysis.problemSolvingScore || 0,
          technicalReasoning: analysis.technicalReasoning,
          communicationReasoning: analysis.communicationReasoning,
          problemSolvingReasoning: analysis.problemSolvingReasoning,
          resumeSummary: analysis.summary,
          resumeHash: fingerprint,
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

        newCandidatesForState.push(candidate);
        processedResults.push({ name: file.name, ...analysis, isDuplicate: !!duplicateMatch });
      } catch (err) {
        console.error(`Failed to process ${file.name}`, err);
        processedResults.push({ 
          name: file.name, 
          overallScore: 0, 
          summary: "Error: Could not read file content." 
        });
      }
    }
    
    onResults(newCandidatesForState);
    setResults(processedResults);
    setIsScanning(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Batch Resume Screening</h2>
        <button onClick={onComplete} className="text-slate-500 hover:text-slate-700">Cancel</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold">1. Job Description</h3>
            <textarea 
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job requirements here..."
              className="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm font-medium"
            />
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold">2. Upload Resumes</h3>
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer relative">
              <input 
                type="file" 
                multiple 
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
              />
              <div className="space-y-2">
                <svg className="w-12 h-12 text-slate-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-slate-600 font-medium">Click to upload or drag and drop</p>
                <p className="text-xs text-slate-400">Fingerprinting enables high-volume duplicate checks.</p>
              </div>
            </div>
          </div>

          <button 
            disabled={isScanning || !jobDescription || files.length === 0}
            onClick={startScanning}
            className={`w-full py-4 rounded-xl font-black transition-all shadow-lg active:scale-95 ${
              isScanning || !jobDescription || files.length === 0 
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
              : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-100'
            }`}
          >
            {isScanning ? "AI PROCESSING..." : "START INTELLIGENT SCREENING"}
          </button>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm min-h-[500px] flex flex-col">
            <h3 className="font-bold mb-4">Results</h3>
            <div className="space-y-4">
              {results.map((res, i) => (
                <div key={i} className="p-4 border border-slate-100 rounded-xl bg-slate-50 flex items-center justify-between group">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold">{res.name}</span>
                      {res.isDuplicate && (
                        <span className="px-1.5 py-0.5 bg-red-100 text-red-600 text-[8px] font-black uppercase rounded">DUPLICATE</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-1 italic">{res.summary}</p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-lg font-black text-blue-600">{res.overallScore} / 100</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeScanner;
