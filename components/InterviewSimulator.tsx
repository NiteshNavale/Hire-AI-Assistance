
import React, { useState, useEffect, useRef } from 'react';
import { Candidate, InterviewMessage } from '../types';
import { generateInterviewQuestions, evaluateResponse } from '../services/geminiService';

interface InterviewSimulatorProps {
  candidate: Candidate | null;
  onComplete: () => void;
  isPractice?: boolean;
}

const InterviewSimulator: React.FC<InterviewSimulatorProps> = ({ candidate, onComplete, isPractice = false }) => {
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questions, setQuestions] = useState<any[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [sessionPoints, setSessionPoints] = useState(0);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (candidate) {
      initInterview();
    }
  }, [candidate]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initInterview = async () => {
    if (!candidate) return;
    setIsLoading(true);
    try {
      const qs = await generateInterviewQuestions(candidate.name, candidate.role);
      setQuestions(qs);
      
      const welcomeMsg: InterviewMessage = {
        id: 'welcome',
        role: 'interviewer',
        text: isPractice 
          ? `Welcome to Practice Mode! I'll help you prepare for a ${candidate.role} position. I'll ask questions and provide real-time feedback. Ready?`
          : `Hello ${candidate.name}! I'm the HireAI Assistant. Today we'll be discussing the ${candidate.role} position. Are you ready to start with the first question?`,
        timestamp: Date.now()
      };
      setMessages([welcomeMsg]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const askNextQuestion = () => {
    if (currentQuestionIndex < questions.length) {
      const q = questions[currentQuestionIndex];
      const newMsg: InterviewMessage = {
        id: `q-${currentQuestionIndex}`,
        role: 'interviewer',
        text: q.question,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, newMsg]);
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      const bonus = isPractice ? 50 : 100;
      setSessionPoints(prev => prev + bonus);
      
      const finishMsg: InterviewMessage = {
        id: 'finish',
        role: 'interviewer',
        text: isPractice 
          ? `Great job! You've earned ${sessionPoints + bonus} points in this practice session. Keep it up!`
          : `Thank you for your time, ${candidate?.name}. We have concluded the automated part of the interview. Our team will review the AI evaluation shortly.`,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, finishMsg]);
    }
  };

  const handleSend = async () => {
    if (!userInput.trim()) return;

    const userMsg: InterviewMessage = {
      id: `u-${Date.now()}`,
      role: 'candidate',
      text: userInput,
      timestamp: Date.now()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setUserInput('');
    
    if (currentQuestionIndex > 0 && currentQuestionIndex <= questions.length) {
      setIsEvaluating(true);
      const prevQ = questions[currentQuestionIndex - 1];
      try {
        const evalResult = await evaluateResponse(prevQ.question, userInput);
        
        // Award points based on score
        const pointsEarned = Math.round(evalResult.score / 2);
        setSessionPoints(prev => prev + pointsEarned);

        if (isPractice) {
          const feedbackMsg: InterviewMessage = {
            id: `f-${Date.now()}`,
            role: 'interviewer',
            text: `📝 Feedback: ${evalResult.feedback}\n\n✨ Clarity: ${evalResult.clarity}\n✨ Conciseness: ${evalResult.conciseness}\n✨ Relevance: ${evalResult.relevance}\n\n💡 Try: ${evalResult.suggestedImprovement}\n\n🏆 Points Earned: +${pointsEarned}`,
            timestamp: Date.now(),
            feedback: evalResult
          };
          setMessages(prev => [...prev, feedbackMsg]);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setIsEvaluating(false);
        setTimeout(askNextQuestion, isPractice ? 3000 : 1000); // More time to read feedback in practice
      }
    } else {
      setTimeout(askNextQuestion, 800);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-slate-500 font-medium">Preparing role-specific questions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto h-[80vh] flex flex-col gap-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={onComplete} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          </button>
          <div>
            <h2 className="text-xl font-bold">{isPractice ? 'Practice Session' : 'Official Interview'}</h2>
            <p className="text-sm text-slate-500">{candidate?.role} Pipeline</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-100 rounded-full">
            <span className="text-amber-600 font-black">★ {sessionPoints}</span>
            <span className="text-[10px] font-bold text-amber-500 uppercase">Points</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
            <span className="text-sm font-semibold text-slate-700">LIVE EVALUATION</span>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-hidden">
        {/* Chat Area */}
        <div className="md:col-span-2 bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto space-y-4">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === 'interviewer' ? 'justify-start' : 'justify-end'}`}>
                <div className={`max-w-[80%] p-4 rounded-2xl whitespace-pre-wrap ${
                  m.role === 'interviewer' 
                  ? (m.feedback ? 'bg-blue-50 border border-blue-100 text-blue-900 rounded-tl-none italic' : 'bg-slate-100 text-slate-800 rounded-tl-none')
                  : 'bg-blue-600 text-white rounded-tr-none shadow-md'
                }`}>
                  <p className="text-sm leading-relaxed">{m.text}</p>
                  <p className={`text-[10px] mt-1 ${m.role === 'interviewer' ? 'text-slate-400' : 'text-blue-200'}`}>
                    {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            {isEvaluating && (
              <div className="flex justify-start">
                <div className="bg-slate-100 p-4 rounded-2xl rounded-tl-none animate-pulse text-slate-400 text-sm">
                  AI is evaluating your response...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-4 bg-slate-50 border-t border-slate-200">
            <div className="flex gap-4">
              <input 
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Type your response here..."
                disabled={isEvaluating}
                className="flex-1 p-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
              />
              <button 
                onClick={handleSend}
                disabled={isEvaluating || !userInput.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white p-3 rounded-xl transition-all shadow-lg shadow-blue-100"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
              </button>
            </div>
          </div>
        </div>

        {/* Video Simulation & Progress */}
        <div className="space-y-6">
          <div className="bg-slate-900 rounded-3xl overflow-hidden aspect-video relative shadow-xl group">
            <img 
              src={`https://picsum.photos/seed/${candidate?.id}/800/450`} 
              className="w-full h-full object-cover opacity-80" 
              alt="Candidate Video Feed" 
            />
            <div className="absolute top-4 right-4 flex gap-2">
              <div className="bg-white/20 backdrop-blur-md px-2 py-1 rounded text-[10px] text-white font-bold tracking-widest uppercase">
                4K UHD
              </div>
            </div>
            <div className="absolute bottom-4 left-4 flex items-center gap-3">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-ping"></div>
              <p className="text-white text-xs font-bold drop-shadow-md">{candidate?.name}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800">Session Progress</h3>
            <div className="space-y-3">
              {questions.map((q, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    i < currentQuestionIndex - 1 ? 'bg-green-100 text-green-700' : 
                    i === currentQuestionIndex - 1 ? 'bg-blue-600 text-white animate-pulse' : 
                    'bg-slate-100 text-slate-400'
                  }`}>
                    {i < currentQuestionIndex - 1 ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                    ) : (i + 1)}
                  </div>
                  <div className="flex-1">
                    <p className={`text-xs font-bold ${i === currentQuestionIndex - 1 ? 'text-blue-600' : 'text-slate-500'}`}>
                      {q.category}
                    </p>
                    <div className="w-full bg-slate-100 h-1 rounded-full mt-1">
                      <div className={`h-full rounded-full transition-all duration-1000 ${
                         i < currentQuestionIndex - 1 ? 'bg-green-500 w-full' : 
                         i === currentQuestionIndex - 1 ? 'bg-blue-500 w-1/2' : 'w-0'
                      }`}></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-600 to-blue-700 p-6 rounded-3xl text-white space-y-2 shadow-lg shadow-indigo-100">
            <p className="text-xs font-bold opacity-80 uppercase tracking-wider">AI Coach Note</p>
            <p className="text-sm font-medium leading-relaxed">
              {isPractice ? "Take your time to structure your response using the STAR method. I'll provide feedback on how to improve your impact statements." : "Candidate is performing significantly above average in technical precision."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewSimulator;
