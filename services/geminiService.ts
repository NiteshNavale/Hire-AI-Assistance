
import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

/**
 * Generates a consistent numeric seed from a string to ensure
 * deterministic LLM outputs for identical inputs.
 */
const getDeterministicSeed = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
};

export const screenResume = async (resumeText: string, jobDescription: string) => {
  // Use strictly the resume and job desc for the seed to ensure stability
  const seedString = `${jobDescription.trim().toLowerCase()}_${resumeText.trim()}`;
  const seed = getDeterministicSeed(seedString);

  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: `Acting as a deterministic and objective technical recruiter, perform a deep analysis of the following resume against the job requirements.
    
    CRITICAL INSTRUCTION:
    1. Your analysis must be consistent. Identical resumes for the same job must yield identical scores.
    2. All scores MUST be integers between 0 and 100.
    3. Evaluate strictly based on the provided text.

    Job Requirements: ${jobDescription}
    Resume Content: ${resumeText}`,
    config: {
      temperature: 0, // Absolute zero for maximum determinism
      seed: seed,     // Fixed seed based on content
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          overallScore: { type: Type.INTEGER, description: "Final match score (0-100)" },
          technicalScore: { type: Type.INTEGER, description: "Technical proficiency (0-100)" },
          communicationScore: { type: Type.INTEGER, description: "Communication clarity (0-100)" },
          problemSolvingScore: { type: Type.INTEGER, description: "Logic and reasoning (0-100)" },
          technicalReasoning: { type: Type.STRING },
          communicationReasoning: { type: Type.STRING },
          problemSolvingReasoning: { type: Type.STRING },
          summary: { type: Type.STRING },
          strengths: { type: Type.ARRAY, items: { type: Type.STRING } },
          weaknesses: { type: Type.ARRAY, items: { type: Type.STRING } }
        },
        required: ["overallScore", "summary", "technicalScore", "communicationScore", "problemSolvingScore", "technicalReasoning", "communicationReasoning", "problemSolvingReasoning"]
      }
    }
  });
  
  try {
    const data = JSON.parse(response.text);
    
    // Safety: Force all scores to integers to prevent decimals in the UI
    return {
      ...data,
      overallScore: Math.round(Number(data.overallScore) || 0),
      technicalScore: Math.round(Number(data.technicalScore) || 0),
      communicationScore: Math.round(Number(data.communicationScore) || 0),
      problemSolvingScore: Math.round(Number(data.problemSolvingScore) || 0),
    };
  } catch (e) {
    console.error("Failed to parse AI response", e);
    throw e;
  }
};

export const generateInterviewQuestions = async (candidateName: string, role: string) => {
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: `Generate 5 relevant interview questions for ${candidateName} applying for the role of ${role}.`,
    config: {
      temperature: 0,
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            question: { type: Type.STRING },
            category: { type: Type.STRING },
            intent: { type: Type.STRING }
          }
        }
      }
    }
  });
  return JSON.parse(response.text);
};

export const evaluateResponse = async (question: string, responseText: string) => {
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: `Evaluate the following interview response out of 100.
    Question: ${question}
    Response: ${responseText}`,
    config: {
      temperature: 0,
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          score: { type: Type.INTEGER },
          feedback: { type: Type.STRING },
          clarity: { type: Type.STRING },
          conciseness: { type: Type.STRING },
          relevance: { type: Type.STRING },
          suggestedImprovement: { type: Type.STRING }
        },
        required: ["score", "feedback", "clarity", "conciseness", "relevance"]
      }
    }
  });
  const data = JSON.parse(response.text);
  return {
    ...data,
    score: Math.round(Number(data.score) || 0)
  };
};
