
export type CandidateStatus = 'Screening' | 'Interviewing' | 'Evaluated' | 'Hired' | 'Rejected';

export interface Badge {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
}

export interface SkillScore {
  name: string;
  score: number;
  max: number;
  reason?: string;
}

export interface Candidate {
  id: string;
  name: string;
  role: string;
  email: string;
  status: CandidateStatus;
  overallScore: number;
  technicalScore: number;
  communicationScore: number;
  problemSolvingScore: number;
  technicalReasoning?: string;
  communicationReasoning?: string;
  problemSolvingReasoning?: string;
  resumeSummary: string;
  skills: SkillScore[];
  points: number;
  badges: string[];
  interviewDate?: string;
  interviewTime?: string;
  isDuplicate?: boolean;
  duplicateOf?: string;
  resumeHash?: string;
  accessKey?: string; // Unique key for candidate login
  gapAnalysis: {
    skill: string;
    gap: string;
    priority: 'Low' | 'Medium' | 'High';
  }[];
  trainingPath: {
    title: string;
    provider: string;
    duration: string;
    type: 'Course' | 'Certification' | 'Reading';
    completed?: boolean;
  }[];
}

export interface InterviewMessage {
  id: string;
  role: 'interviewer' | 'candidate';
  text: string;
  timestamp: number;
  feedback?: {
    score: number;
    clarity: string;
    conciseness: string;
    relevance: string;
    improvement: string;
  };
}

export const BADGES: Record<string, Badge> = {
  'smooth_talker': { id: 'smooth_talker', name: 'Smooth Talker', icon: '💬', color: 'bg-emerald-100 text-emerald-700', description: 'Exceptional communication skills' },
  'tech_wizard': { id: 'tech_wizard', name: 'Tech Wizard', icon: '🧙‍♂️', color: 'bg-purple-100 text-purple-700', description: 'Scored 95+ in technical evaluation' },
  'problem_solver': { id: 'problem_solver', name: 'Problem Solver', icon: '🧩', color: 'bg-blue-100 text-blue-700', description: 'Handled complex logic questions with ease' },
  'quick_learner': { id: 'quick_learner', name: 'Quick Learner', icon: '⚡', color: 'bg-amber-100 text-amber-700', description: 'Completed first training module' }
};
