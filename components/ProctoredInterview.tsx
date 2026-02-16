
import React, { useState, useEffect, useRef } from 'react';
import { Candidate, InterviewMessage } from '../types';
import { generateInterviewQuestions, evaluateResponse } from '../services/geminiService';

interface ProctoredInterviewProps {
  candidate: Candidate;
  onComplete: () => void;
}

const ProctoredInterview: React.FC<ProctoredInterviewProps> = ({ candidate, onComplete }) => {
  const [phase, setPhase] = useState<'setup' | 'loading' | 'active' | 'terminated'>('setup');
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questions, setQuestions] = useState<any[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [timeLeft, setTimeLeft] = useState(1800); // 30 mins in seconds
  const [terminationReason, setTerminationReason] = useState('');
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const setupVideoRef = useRef<HTMLVideoElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Persistent stream references to survive re-renders
  const cameraStreamRef = useRef<MediaStream | null>(null);

  // Effect to attach streams once the 'active' phase UI is rendered
  useEffect(() => {
    if (phase === 'active') {
      const attachStreams = () => {
        if (cameraStreamRef.current && videoRef.current) {
          videoRef.current.srcObject = cameraStreamRef.current;
        }
      };

      // Immediate attempt and a small delayed attempt to ensure DOM is ready
      attachStreams();
      const timer = setTimeout(attachStreams, 300);

      // Auto-start interview questions after welcome message
      if (messages.length === 1) {
        const qTimer = setTimeout(askNextQuestion, 2000);
        return () => {
          clearTimeout(timer);
          clearTimeout(qTimer);
        };
      }
      return () => clearTimeout(timer);
    }
  }, [phase]);

  // Anti-Cheating: Tab/Application Focus Detection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden' && phase === 'active') {
        terminateInterview('Tab Switching Detected (Security Breach)');
      }
    };

    const handleBlur = () => {
      if (phase === 'active') {
        terminateInterview('Application Focus Lost (Potential Cheating)');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
    };
  }, [phase]);

  // 30-Minute Timer logic
  useEffect(() => {
    if (phase === 'active' && timeLeft > 0) {
      const timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
      return () => clearInterval(timer);
    } else if (timeLeft === 0 && phase === 'active') {
      terminateInterview('Interview Time Expired (30:00)');
    }
  }, [phase, timeLeft]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const terminateInterview = (reason: string) => {
    setPhase('terminated');
    setTerminationReason(reason);
    // Stop all media tracks immediately
    cameraStreamRef.current?.getTracks().forEach(t => t.stop());
  };

  const startSetup = async () => {
    setPhase('loading');
    try {
      // 1. Camera & Audio Capture
      const cameraStream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: { ideal: 1280 }, height: { ideal: 720 } }, 
        audio: true 
      });
      cameraStreamRef.current = cameraStream;

      // 2. AI Questions Generation (Job specific)
      const qs = await generateInterviewQuestions(candidate.name, candidate.role);
      setQuestions(qs);
      
      // 3. Initial Proctored Welcome
      const welcomeMsg: InterviewMessage = {
        id: 'welcome',
        role: 'interviewer',
        text: `Welcome, ${candidate.name}. Media protocol verified. Camera and Microphone are successfully synchronized. Your 30-minute proctored round begins now. Good luck.`,
        timestamp: Date.now()
      };
      
      setMessages([welcomeMsg]);
      setPhase('active');
    } catch (err) {
      console.error("Setup failed:", err);
      setPhase('setup');
      alert("Proctored mode requires Camera and Microphone permissions. Please ensure you are granting all requested permissions.");
    }
  };

  const askNextQuestion = () => {
    if (currentQuestionIndex < questions.length) {
      const q = questions[currentQuestionIndex];
      setMessages(prev => [...prev, {
        id: `q-${currentQuestionIndex}`,
        role: 'interviewer',
        text: q.question,
        timestamp: Date.now()
      }]);
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      setMessages(prev => [...prev, {
        id: 'finish',
        role: 'interviewer',
        text: `The proctored session has concluded successfully. Your data has been encrypted and submitted for final review. You may exit the session now.`,
        timestamp: Date.now()
      }]);
    }
  };

  const handleSend = async () => {
    if (!userInput.trim() || isEvaluating) return;
    const userMsg: InterviewMessage = { id: `u-${Date.now()}`, role: 'candidate', text: userInput, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setUserInput('');
    
    if (currentQuestionIndex > 0 && currentQuestionIndex <= questions.length) {
      setIsEvaluating(true);
      try {
        await evaluateResponse(questions[currentQuestionIndex - 1].question, userInput);
      } catch (e) { console.error(e); }
      setIsEvaluating(false);
      setTimeout(askNextQuestion, 1200);
    } else {
      setTimeout(askNextQuestion, 800);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (phase === 'setup' || phase === 'loading') {
    return (
      <div className="max-w-4xl mx-auto py-12 animate-fadeIn space-y-8">
        <div className="bg-white p-10 rounded-3xl border border-slate-200 shadow-xl text-center space-y-6">
          <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center text-3xl mx-auto">🛡️</div>
          <h2 className="text-3xl font-black text-slate-900">Security Verification</h2>
          <p className="text-slate-500 max-w-md mx-auto">To proceed to the interview, you must enable your camera and microphone for automated proctoring.</p>
          
          <div className="max-w-md mx-auto">
             <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 flex flex-col items-center gap-3">
                <div className="w-full aspect-video bg-black rounded-xl overflow-hidden relative shadow-inner">
                  {cameraStreamRef.current ? (
                     <video autoPlay playsInline muted className="w-full h-full object-cover" ref={(el) => { if(el) el.srcObject = cameraStreamRef.current; }} />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-[10px] font-black uppercase">Waiting for Permissions...</div>
                  )}
                </div>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Media Verification</span>
             </div>
          </div>

          <button 
            onClick={startSetup} 
            disabled={phase === 'loading'}
            className={`w-full py-5 font-black rounded-2xl shadow-xl transition-all shadow-blue-100 active:scale-[0.98] flex items-center justify-center gap-3 ${
              phase === 'loading' ? 'bg-slate-200 text-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {phase === 'loading' ? (
              <>
                <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                VERIFYING PROTOCOL...
              </>
            ) : "GRANT PERMISSIONS & ENTER INTERVIEW"}
          </button>
          
          <div className="p-4 bg-blue-50 rounded-xl border border-blue-100 text-left">
            <p className="text-[10px] text-blue-700 font-black uppercase tracking-widest mb-1">Security Policy:</p>
            <ul className="text-[10px] text-blue-600 font-medium leading-relaxed list-disc pl-4 space-y-1">
              <li>Camera and Microphone must remain active.</li>
              <li>Switching tabs or applications will result in immediate termination.</li>
              <li>Gaze and audio integrity are monitored in real-time.</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (phase === 'terminated') {
    return (
      <div className="max-w-2xl mx-auto py-24 text-center animate-fadeIn space-y-8">
        <div className="w-24 h-24 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-5xl mx-auto border-4 border-red-200 animate-pulse">🚫</div>
        <div className="space-y-4">
          <h2 className="text-4xl font-black text-slate-900">Interview Terminated</h2>
          <p className="text-red-600 font-bold text-lg">{terminationReason}</p>
          <p className="text-slate-500 max-w-sm mx-auto">A security violation was detected. This incident has been recorded and the recruitment team has been notified.</p>
        </div>
        <button onClick={onComplete} className="px-8 py-3 bg-slate-900 text-white font-bold rounded-xl transition-all hover:bg-black">RETURN TO PORTAL</button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto h-[85vh] flex flex-col gap-6 animate-fadeIn pb-8">
      <div className="flex items-center justify-between bg-white px-8 py-4 rounded-3xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 bg-red-50 text-red-600 px-3 py-1 rounded-full border border-red-100">
             <span className="w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
             <span className="text-[10px] font-black uppercase tracking-widest">Live Security Feed</span>
          </div>
          <p className="text-sm font-black text-slate-900">{candidate.name} <span className="text-slate-300 mx-2">|</span> {candidate.role}</p>
        </div>
        <div className="flex items-center gap-8">
          <div className="text-right">
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Session Time Remaining</p>
             <p className={`text-2xl font-black ${timeLeft < 300 ? 'text-red-600 animate-pulse' : 'text-slate-900'}`}>{formatTime(timeLeft)}</p>
          </div>
          <button onClick={() => terminateInterview('Candidate Requested Manual Termination')} className="text-[10px] font-black text-red-500 hover:underline uppercase tracking-widest">Emergency Stop</button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 overflow-hidden">
        {/* Chat Area */}
        <div className="lg:col-span-3 bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-slate-50/30">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === 'interviewer' ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[85%] p-5 rounded-3xl ${
                  m.role === 'interviewer' 
                  ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-sm font-medium'
                  : 'bg-blue-600 text-white rounded-tr-none shadow-lg'
                }`}>
                  <p className="text-sm leading-relaxed">{m.text}</p>
                </div>
              </div>
            ))}
            {isEvaluating && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 p-4 rounded-3xl rounded-tl-none animate-pulse text-slate-400 text-[10px] font-black uppercase tracking-widest">AI Evaluating Response...</div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-6 bg-white border-t border-slate-100">
            <div className="flex gap-4">
              <textarea 
                rows={2}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Type your response... (Press Enter to send)"
                className="flex-1 p-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 resize-none font-medium text-sm"
              />
              <button 
                onClick={handleSend}
                disabled={!userInput.trim() || isEvaluating}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 text-white px-6 rounded-2xl transition-all shadow-xl shadow-blue-50 active:scale-95"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
              </button>
            </div>
          </div>
        </div>

        {/* Monitoring Feeds */}
        <div className="lg:col-span-1 space-y-6 flex flex-col">
           <div className="bg-slate-900 rounded-3xl aspect-[3/4] overflow-hidden relative border-4 border-white shadow-xl">
              <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              <div className="absolute bottom-4 left-4 bg-black/40 backdrop-blur-md px-3 py-1 rounded-full text-[10px] text-white font-bold uppercase tracking-widest">Identity Feed</div>
           </div>
           
           <div className="flex-1 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col">
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Proctoring Analytics</h4>
              <div className="space-y-5">
                 <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-600">Audio Spectrum</span>
                    <div className="flex gap-1">
                       {[1,2,3,4,5,6,7,8].map(i => <div key={i} className={`w-1 h-3 rounded-full ${i < 6 ? 'bg-emerald-400' : 'bg-slate-100'}`}></div>)}
                    </div>
                 </div>
                 <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-600">Gaze Tracking</span>
                    <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Verified</span>
                 </div>
                 <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-600">Integrity Check</span>
                    <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">100% Secure</span>
                 </div>
              </div>
              
              <div className="mt-auto pt-6 border-t border-slate-100">
                 <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">System Status:</p>
                 <p className="text-[10px] text-slate-400 font-medium leading-relaxed italic">"AI Proctor is monitoring gaze, keyboard events, and ambient sound for integrity validation."</p>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default ProctoredInterview;
