// frontend/src/app/jobs/analysis/page.tsx
// Next.js page view displaying structured job intelligence, skills category, and ATS keyword audits

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '../../../store/authStore';
import { useAuth } from '../../../hooks/useAuth';

interface Skill {
  name: string;
  category: string;
  importance: string;
}

interface ATSKeyword {
  word: string;
  category: string;
}

interface JobMetadata {
  seniority: string;
  employment_type: string;
  education_requirements: string | null;
  certifications: string[];
}

interface JobAnalysisData {
  id: string;
  job_id: string;
  confidence_score: number;
  llm_provider: string;
  prompt_version: string;
  processing_time_ms: number;
  metadata: JobMetadata;
  skills: Skill[];
  ats_keywords: ATSKeyword[];
  responsibilities: string[];
  qualifications: string[];
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function JobAnalysisPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const job_id = searchParams.get('job_id');

  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  const [analysis, setAnalysis] = useState<JobAnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const triggerJobAnalysis = async () => {
    if (!accessToken || !job_id) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/jobs/analysis/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ job_id })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'AI Job analysis failed.');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to trigger job analysis.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (!job_id) {
      router.push('/jobs');
      return;
    }
    triggerJobAnalysis();
  }, [isAuthenticated, job_id, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sidebar Mock */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col justify-between hidden md:flex">
        <div>
          <div className="mb-8 font-extrabold text-2xl tracking-tight text-white font-sans">
            AI Job <span className="text-indigo-500">Copilot</span>
          </div>
          <nav className="space-y-2">
            <button 
              onClick={() => router.push('/dashboard')}
              className="w-full text-left px-4 py-2.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 font-semibold transition-all"
            >
              Dashboard
            </button>
            <button 
              onClick={() => router.push('/resume')}
              className="w-full text-left px-4 py-2.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 font-semibold transition-all"
            >
              Resume Workspace
            </button>
            <button 
              onClick={() => router.push('/jobs')}
              className="w-full text-left px-4 py-2.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 font-semibold transition-all"
            >
              Job Parser Workspace
            </button>
            <button 
              className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold"
            >
              Job Analysis View
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-5xl overflow-y-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white font-sans">
              AI Job Understanding details
            </h1>
            <p className="mt-1 text-slate-400 text-sm">
              Structured requirement criteria extracted by the AI Engine.
            </p>
          </div>
          <button
            onClick={() => router.push('/jobs')}
            className="px-4 py-2 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all self-start"
          >
            Back to Ingestion
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center space-x-2 text-slate-500">
            <span className="w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></span>
            <span>AI model parsing job text requirements...</span>
          </div>
        ) : errorMessage ? (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-xl">
            {errorMessage}
          </div>
        ) : !analysis ? (
          <div className="text-slate-500">No analysis metadata retrieved.</div>
        ) : (
          <div className="space-y-8">
            {/* Metadata Summary & Engine Audit Card */}
            <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-sm">
                <div>
                  <span className="block text-slate-500 text-xs">Seniority</span>
                  <span className="font-bold text-slate-100">{analysis.metadata.seniority}</span>
                </div>
                <div>
                  <span className="block text-slate-500 text-xs">Employment Type</span>
                  <span className="font-bold text-slate-100">{analysis.metadata.employment_type}</span>
                </div>
                <div>
                  <span className="block text-slate-500 text-xs">LLM Provider</span>
                  <span className="font-bold text-slate-100 uppercase">{analysis.llm_provider}</span>
                </div>
                <div>
                  <span className="block text-slate-500 text-xs">Processing Time</span>
                  <span className="font-bold text-slate-100">{analysis.processing_time_ms} ms</span>
                </div>
              </div>
              <div className="flex items-center space-x-2 bg-indigo-950/20 border border-indigo-900/50 rounded-xl px-4 py-2 self-start sm:self-center">
                <span className="text-indigo-400 font-bold text-lg">{(analysis.confidence_score * 100).toFixed(0)}%</span>
                <span className="text-slate-400 text-xs leading-none">AI Confidence Score</span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
              {/* Left Column: Skills & ATS Keywords */}
              <div className="lg:col-span-2 space-y-8">
                {/* Skills */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <h3 className="text-xl font-bold text-slate-100 font-sans">Extracted Technical Skills</h3>
                  <div className="space-y-4">
                    {/* Category grouping */}
                    {Array.from(new Set(analysis.skills.map((s) => s.category))).map((category) => (
                      <div key={category} className="space-y-2">
                        <span className="text-xs font-semibold uppercase text-slate-500 tracking-wider">{category}</span>
                        <div className="flex flex-wrap gap-2">
                          {analysis.skills.filter((s) => s.category === category).map((skill, index) => (
                            <span 
                              key={index} 
                              className={`px-3 py-1.5 text-xs font-semibold border rounded-lg flex items-center gap-2 ${
                                skill.importance === "Mandatory" 
                                  ? "text-emerald-400 bg-emerald-950/30 border-emerald-900/50" 
                                  : "text-slate-300 bg-slate-950 border-slate-800"
                              }`}
                            >
                              {skill.name}
                              <span className="text-[10px] text-slate-500 uppercase">({skill.importance})</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ATS Keywords */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <h3 className="text-xl font-bold text-slate-100 font-sans">ATS Optimization Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysis.ats_keywords.map((kw, index) => (
                      <span 
                        key={index}
                        className="px-3 py-1.5 text-xs font-medium text-indigo-400 bg-indigo-950/30 border border-indigo-900/50 rounded-lg flex items-center gap-1.5"
                      >
                        {kw.word}
                        <span className="text-[10px] text-slate-500 uppercase">({kw.category})</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column: Responsibilities & Qualifications */}
              <div className="space-y-8">
                {/* Responsibilities */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <h3 className="text-lg font-bold text-slate-100 font-sans">Core Responsibilities</h3>
                  <ul className="space-y-2 text-sm text-slate-400 list-disc list-inside">
                    {analysis.responsibilities.map((resp, index) => (
                      <li key={index} className="leading-relaxed">{resp}</li>
                    ))}
                  </ul>
                </div>

                {/* Qualifications */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                  <h3 className="text-lg font-bold text-slate-100 font-sans">Required Qualifications</h3>
                  <ul className="space-y-2 text-sm text-slate-400 list-disc list-inside">
                    {analysis.qualifications.map((qual, index) => (
                      <li key={index} className="leading-relaxed">{qual}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Next workflow trigger */}
            <div className="flex justify-end pt-4">
              <button
                onClick={() => alert("Proceeding to resume matching and optimization... (Coming in the next phase)")}
                className="px-8 py-3 font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-all shadow-lg"
              >
                Proceed to Match & Tailor
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
