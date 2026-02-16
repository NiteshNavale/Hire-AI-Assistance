
import React, { useState, useEffect } from 'react';
import { Candidate } from '../types';
import { generateAptitudeTest } from '../services/geminiService';

interface ProctoredInterviewProps {
  candidate: Candidate;
  onComplete: () => void;
}

const ProctoredInterview: React.FC<ProctoredInterviewProps> = ({ candidate, onComplete }) => {
  const [phase, setPhase] = useState<'intro' | 'loading' | 'active' | 'finished'>('intro');
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [score, setScore] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState(1200); // 20 minutes
  
  // Load questions on start
  const startExam = async () => {
    setPhase('loading');
    try {
      const qs = await generateAptitudeTest(candidate.role);
      setQuestions(qs);
      setPhase('active');
    } catch (err) {
      console.error("Failed to generate test", err);
      alert("Failed to load aptitude test. Please try again.");
      setPhase('intro');
    }
  };

  // Timer Logic
  useEffect(() => {
    if (phase === 'active' && timeLeft > 0) {
      const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
      return () => clearInterval(timer);
    } else if (timeLeft === 0 && phase === 'active') {
      submitExam();
    }
  }, [phase, timeLeft]);

  const handleOptionSelect = (questionId: number, optionIndex: number) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionIndex }));
  };

  const submitExam = () => {
    let correctCount = 0;
    questions.forEach(q => {
      if (answers[q.id] === q.correctAnswer) {
        correctCount++;
      }
    });
    
    // Calculate percentage score
    const finalScore = Math.round((correctCount / questions.length) * 100);
    setScore(finalScore);
    
    // Here you would typically save the score to the candidate record via an API call
    // For now we just show the finished state
    setPhase('finished');
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (phase === 'intro') {
    return (
      <div className="max-w-4xl mx-auto py-12 animate-fadeIn space-y-8">
        <div className="bg-white p-10 rounded-3xl border border-slate-200 shadow-xl text-center space-y-6">
          <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center text-3xl mx-auto">🧠</div>
          <h2 className="text-3xl font-black text-slate-900">Aptitude & IQ Assessment</h2>
          <p className="text-slate-500 max-w-lg mx-auto">
            This 20-question exam evaluates your Logical Reasoning, Quantitative Aptitude, Verbal Ability, and Technical Knowledge specifically for the <strong>{candidate.role}</strong> role.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
             <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
               <span className="block text-2xl font-black text-slate-700">20</span>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Questions</span>
             </div>
             <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
               <span className="block text-2xl font-black text-slate-700">20m</span>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Time Limit</span>
             </div>
             <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
               <span className="block text-2xl font-black text-slate-700">4</span>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Sections</span>
             </div>
             <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
               <span className="block text-2xl font-black text-slate-700">100%</span>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">AI Generated</span>
             </div>
          </div>

          <button 
            onClick={startExam} 
            className="w-full max-w-md mx-auto py-5 font-black rounded-2xl shadow-xl transition-all shadow-blue-100 active:scale-[0.98] bg-blue-600 hover:bg-blue-700 text-white"
          >
            START ASSESSMENT
          </button>
        </div>
      </div>
    );
  }

  if (phase === 'loading') {
    return (
      <div className="flex items-center justify-center h-[60vh] flex-col gap-4">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-500 font-bold animate-pulse">Generating Aptitude Questions...</p>
      </div>
    );
  }

  if (phase === 'finished') {
    return (
      <div className="max-w-2xl mx-auto py-24 text-center animate-fadeIn space-y-8">
        <div className="w-24 h-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-4xl mx-auto border-4 border-green-200">🏆</div>
        <div className="space-y-4">
          <h2 className="text-4xl font-black text-slate-900">Assessment Complete</h2>
          <div className="text-5xl font-black text-blue-600">{score}%</div>
          <p className="text-slate-500 max-w-sm mx-auto">Your aptitude score has been recorded. The recruitment team will review your application shortly.</p>
        </div>
        <button onClick={onComplete} className="px-8 py-3 bg-slate-900 text-white font-bold rounded-xl transition-all hover:bg-black">RETURN TO DASHBOARD</button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto pb-12 animate-fadeIn space-y-6">
      <div className="flex items-center justify-between bg-white px-8 py-4 rounded-3xl border border-slate-200 shadow-sm sticky top-4 z-10">
        <div>
          <h2 className="text-lg font-black text-slate-900">Aptitude Assessment</h2>
          <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{candidate.role}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`px-4 py-2 rounded-xl font-black text-lg ${timeLeft < 300 ? 'bg-red-50 text-red-600' : 'bg-slate-100 text-slate-700'}`}>
            ⏱ {formatTime(timeLeft)}
          </div>
          <button 
            onClick={submitExam}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl font-bold transition-all"
          >
            Submit Exam
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {questions.map((q, index) => (
          <div key={q.id} className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
             <div className="flex items-center gap-3 mb-4">
                <span className="w-8 h-8 flex items-center justify-center bg-blue-50 text-blue-600 font-black rounded-lg text-sm">{index + 1}</span>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest bg-slate-50 px-2 py-1 rounded">{q.category}</span>
             </div>
             <p className="text-lg font-bold text-slate-800 mb-6">{q.question}</p>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               {q.options.map((opt: string, optIndex: number) => (
                 <label 
                  key={optIndex} 
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-center gap-3 ${
                    answers[q.id] === optIndex 
                    ? 'border-blue-600 bg-blue-50/50' 
                    : 'border-slate-100 hover:border-slate-300 bg-white'
                  }`}
                 >
                   <input 
                    type="radio" 
                    name={`q-${q.id}`} 
                    className="w-5 h-5 text-blue-600"
                    checked={answers[q.id] === optIndex}
                    onChange={() => handleOptionSelect(q.id, optIndex)}
                   />
                   <span className={`text-sm font-medium ${answers[q.id] === optIndex ? 'text-blue-900' : 'text-slate-600'}`}>{opt}</span>
                 </label>
               ))}
             </div>
          </div>
        ))}
      </div>
      
      <div className="flex justify-center pt-8">
        <button 
            onClick={submitExam}
            className="bg-slate-900 hover:bg-black text-white px-12 py-4 rounded-2xl font-black text-lg transition-all shadow-xl shadow-slate-200"
          >
            Submit Final Answers
        </button>
      </div>
    </div>
  );
};

export default ProctoredInterview;
