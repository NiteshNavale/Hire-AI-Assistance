
import React, { useState, useEffect, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import VPDashboard from './components/VPDashboard';
import ResumeScanner from './components/ResumeScanner';
import InterviewSimulator from './components/InterviewSimulator';
import ProctoredInterview from './components/ProctoredInterview';
import EvaluationReport from './components/EvaluationReport';
import PracticeSelector from './components/PracticeSelector';
import Leaderboard from './components/Leaderboard';
import CandidatePortal from './components/CandidatePortal';
import CandidateInterviewAccess from './components/CandidateInterviewAccess';
import OfferLetterView from './components/OfferLetterView';
import Login from './components/Login';
import { Candidate } from './types';
import { MOCK_CANDIDATES } from './constants';

const App: React.FC = () => {
  const [view, setView] = useState<'dashboard' | 'vp-dashboard' | 'screening' | 'interview' | 'proctored' | 'report' | 'practice' | 'leaderboard' | 'apply' | 'login' | 'candidate-login' | 'offer-letter'>('apply');
  const [authToken, setAuthToken] = useState<string | null>(localStorage.getItem('hireai_token'));
  
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [activeCandidateId, setActiveCandidateId] = useState<string | null>(null);
  const [isPracticeMode, setIsPracticeMode] = useState(false);
  const [practiceRole, setPracticeRole] = useState('');

  const handleLogout = useCallback(() => {
    localStorage.removeItem('hireai_token');
    setAuthToken(null);
    setView('apply');
  }, []);

  useEffect(() => {
    const loadInitialData = async () => {
      if (authToken && !authToken.startsWith('local-') && !authToken.startsWith('admin-bypass') && !authToken.startsWith('vp-bypass')) {
        try {
          const res = await fetch('/api/candidates', {
            headers: { 'Authorization': `Bearer ${authToken}` }
          });
          if (res.ok) {
            const data = await res.json();
            setCandidates(data);
            return;
          }
        } catch (e) { console.log("Server unreachable."); }
      }
      
      try {
        const saved = localStorage.getItem('hireai_candidates');
        if (saved) setCandidates(JSON.parse(saved));
      } catch (e) { setCandidates([]); }
    };
    loadInitialData();
  }, [authToken]);

  useEffect(() => {
    if (candidates.length > 0) {
      try {
        localStorage.setItem('hireai_candidates', JSON.stringify(candidates));
      } catch (e) {}
    }
  }, [candidates]);

  const handleLoginSuccess = (token: string) => {
    localStorage.setItem('hireai_token', token);
    setAuthToken(token);
    if (token.startsWith('vp-')) {
        setView('vp-dashboard');
    } else {
        setView('dashboard');
    }
  };

  const activeCandidate = candidates.find(c => c.id === activeCandidateId) || null;

  const handleCandidateAccess = (candidate: Candidate) => {
    setActiveCandidateId(candidate.id);
    if (['Offer Sent', 'Offer Accepted', 'Offer Expired'].includes(candidate.status)) {
        setView('offer-letter');
    } else {
        setView('proctored');
    }
  };

  const renderContent = () => {
    switch (view) {
      case 'login': return <Login onLoginSuccess={handleLoginSuccess} />;
      case 'candidate-login': return <CandidateInterviewAccess candidates={candidates} onLogin={handleCandidateAccess} />;
      case 'dashboard': return <Dashboard 
          candidates={candidates} 
          authToken={authToken}
          onViewCandidate={(id) => { setActiveCandidateId(id); setView('report'); }}
          onStartInterview={(id) => { setActiveCandidateId(id); setView('interview'); }}
          onStartScreening={() => setView('screening')}
          onUpdateCandidate={(id, updates) => setCandidates(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c))}
        />;
      case 'vp-dashboard': return <VPDashboard 
          candidates={candidates}
          onUpdateCandidate={(id, updates) => setCandidates(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c))}
          onLogout={handleLogout}
      />;
      case 'apply': return <CandidatePortal onApply={(c) => setCandidates(prev => [c, ...prev])} existingCandidates={candidates} />;
      case 'screening': return <ResumeScanner onComplete={() => setView('dashboard')} existingCandidates={candidates} onResults={(newOnes) => setCandidates(prev => [...newOnes, ...prev])} />;
      case 'proctored': return activeCandidate ? <ProctoredInterview candidate={activeCandidate} onComplete={() => setView('apply')} /> : null;
      case 'interview': return <InterviewSimulator candidate={activeCandidate} onComplete={() => setView('dashboard')} />;
      case 'report': return <EvaluationReport candidate={activeCandidate} onBack={() => setView('dashboard')} />;
      case 'offer-letter': return activeCandidate ? <OfferLetterView 
          candidate={activeCandidate} 
          onAccept={() => setCandidates(prev => prev.map(c => c.id === activeCandidateId ? { ...c, status: 'Offer Accepted', offerLetter: { ...c.offerLetter!, isAccepted: true } } : c))}
          onLogout={() => setView('apply')}
      /> : null;
      case 'practice': return <PracticeSelector onStart={(role) => {
          const dummy: Candidate = { ...MOCK_CANDIDATES[0], id: 'practice-user', name: 'Practice Mode User', role, status: 'Screening', email: 'practice@hireai.com', overallScore: 0, technicalScore: 0, communicationScore: 0, problemSolvingScore: 0, resumeSummary: '', points: 0, badges: [], skills: [], gapAnalysis: [], trainingPath: [] };
          setCandidates(prev => [...prev.filter(c => c.id !== 'practice-user'), dummy]);
          setActiveCandidateId('practice-user');
          setView('interview');
      }} />;
      default: return <CandidatePortal onApply={(c) => setCandidates(prev => [c, ...prev])} existingCandidates={candidates} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => setView('apply')}>
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">H</div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">HireAI</h1>
            </div>
            <div className="flex bg-slate-100 p-1 rounded-xl">
               <button onClick={() => setView('apply')} className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest transition-all ${view === 'apply' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500'}`}>APPLY</button>
               <button onClick={() => setView('candidate-login')} className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest transition-all ${view === 'candidate-login' || view === 'proctored' || view === 'offer-letter' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500'}`}>CANDIDATE LOGIN</button>
               <button onClick={() => authToken ? (authToken.startsWith('vp-') ? setView('vp-dashboard') : setView('dashboard')) : setView('login')} className={`px-4 py-1.5 rounded-lg text-[10px] font-black tracking-widest transition-all ${authToken || view === 'dashboard' || view === 'vp-dashboard' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-500'}`}>HR PORTAL</button>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {authToken ? (
              <button onClick={handleLogout} className="text-[10px] font-black text-red-500 hover:text-red-700 uppercase tracking-widest bg-red-50 px-3 py-1.5 rounded-lg">Logout</button>
            ) : (
              <button onClick={() => setView('login')} className="text-[10px] font-black text-blue-600 hover:text-blue-800 uppercase tracking-widest">Login</button>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full p-4 md:p-8">
        {renderContent()}
      </main>
    </div>
  );
};

export default App;
