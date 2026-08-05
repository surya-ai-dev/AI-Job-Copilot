// frontend/src/app/resume/optimization/page.tsx
// Next.js page view displaying match scores, ATS improvements, and recommendation reports

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '../../../store/authStore';
import { useAuth } from '../../../hooks/useAuth';

interface Recommendation {
  section: string;
  change_type: string;
  description: string;
  original_text: string | null;
  suggested_text: string | null;
}

interface ATSReport {
  score: number;
  explanation: string;
  keyword_coverage_percent: number;
  readability_index: number;
}

interface MatchDetails {
  match_score: number;
  skills_match_score: number;
  experience_match_score: number;
  gap_skills: string[];
}

interface OptimizationData {
  id: string;
  resume_id: string;
  job_analysis_id: string;
  match_score: number;
  ats_score: number;
  optimized_summary: string;
  optimized_skills: string[];
  match_details: MatchDetails;
  ats_evaluation: ATSReport;
  recommendations: Recommendation[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function OptimizationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const job_analysis_id = searchParams.get('job_analysis_id');

  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  const [optData, setOptData] = useState<OptimizationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const triggerOptimization = async () => {
    if (!accessToken || !job_analysis_id) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/resume/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ job_analysis_id })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Resume optimization failed.');
      }

      const data = await response.json();
      setOptData(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to trigger optimization.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (!job_analysis_id) {
      router.push('/resume');
      return;
    }
    triggerOptimization();
  }, [isAuthenticated, job_analysis_id, router]);

  const handleDownloadClick = () => {
    if (!optData || !accessToken) return;
    window.open(`${API_BASE_URL}/resume/optimize/download/${optData.id}?token=${accessToken}`, '_blank');
  };

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
              className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold"
            >
              Optimization Report
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-5xl overflow-y-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white font-sans">
              Resume Optimization Report
            </h1>
            <p className="mt-1 text-slate-400 text-sm">
              Tailored summary, keywords alignment, and ATS metrics audit details.
            </p>
          </div>
          <button
            onClick={() => router.push('/resume')}
            className="px-4 py-2 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all self-start"
          >
            Back to Workspace
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center space-x-2 text-slate-500">
            <span className="w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></span>
            <span>Running AI optimization matching loop iterations...</span>
          </div>
        ) : errorMessage ? (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-xl">
            {errorMessage}
          </div>
        ) : !optData ? (
          <div className="text-slate-500">No optimization metadata retrieved.</div>
        ) : (
          <div className="space-y-8">
            {/* Score Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Semantic Match Score */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between shadow-xl">
                <div>
                  <span className="block text-slate-500 text-xs">Semantic Match</span>
                  <span className="text-sm font-semibold text-slate-400">Skills & experience alignment</span>
                </div>
                <div className="text-indigo-400 font-extrabold text-3xl">
                  {optData.match_score}%
                </div>
              </div>

              {/* Estimated ATS Score */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between shadow-xl">
                <div>
                  <span className="block text-slate-500 text-xs">Estimated ATS Score</span>
                  <span className="text-sm font-semibold text-slate-400">Keyword parser compatibility</span>
                </div>
                <div className="text-emerald-400 font-extrabold text-3xl">
                  {optData.ats_score}%
                </div>
              </div>

              {/* Action Downloads */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col justify-center gap-2 shadow-xl">
                <button
                  onClick={handleDownloadClick}
                  className="w-full py-2.5 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-all text-center"
                >
                  Download Optimized PDF
                </button>
              </div>
            </div>

            {/* In-depth reports grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
              {/* Summary and Skills Preview */}
              <div className="lg:col-span-2 space-y-8">
                {/* Summary */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
                  <h3 className="text-xl font-bold text-slate-100 font-sans">Optimized Summary Statement</h3>
                  <p className="text-slate-300 text-sm leading-relaxed p-4 bg-slate-950 border border-slate-800 rounded-xl">
                    {optData.optimized_summary}
                  </p>
                </div>

                {/* Skills */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
                  <h3 className="text-xl font-bold text-slate-100 font-sans">Prioritized Skills List</h3>
                  <div className="flex flex-wrap gap-2">
                    {optData.optimized_skills.map((skill, index) => (
                      <span 
                        key={index}
                        className="px-3 py-1.5 text-xs font-semibold text-indigo-400 bg-indigo-950/20 border border-indigo-900/50 rounded-lg"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommendations and Gaps */}
              <div className="space-y-8">
                {/* Recommendations */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
                  <h3 className="text-lg font-bold text-slate-100 font-sans">Optimization Checklist</h3>
                  <div className="space-y-4">
                    {optData.recommendations.map((rec, index) => (
                      <div key={index} className="space-y-1 text-sm border-b border-slate-800 pb-3 last:border-0 last:pb-0">
                        <span className="text-xs font-semibold uppercase text-indigo-400">{rec.section} • {rec.change_type}</span>
                        <p className="text-slate-300">{rec.description}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Missing Gap Skills */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
                  <h3 className="text-lg font-bold text-slate-100 font-sans">Unmatched Skills Gaps</h3>
                  <p className="text-xs text-slate-500">
                    The following required skills were not found on your master resume. The AI will not fabricate experience to match them.
                  </p>
                  <div className="flex flex-wrap gap-1.5 pt-2">
                    {optData.match_details.gap_skills.map((skill, index) => (
                      <span 
                        key={index}
                        className="px-2.5 py-1 text-xs font-medium text-red-400 bg-red-950/20 border border-red-900/30 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Next workflow trigger */}
            <div className="flex justify-end pt-4">
              <button
                onClick={() => alert("Proceeding to outreach email generation... (Coming in the next phase)")}
                className="px-8 py-3 font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-all shadow-lg"
              >
                Proceed to Recruiter Outreach
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
