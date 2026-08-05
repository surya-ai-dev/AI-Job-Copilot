// frontend/src/app/outreach/pipeline/page.tsx
// Next.js page view orchestrating the complete end-to-end job ingestion, analysis, & optimization pipeline wizard

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../../store/authStore';
import { useAuth } from '../../../hooks/useAuth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function PipelineWizardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  // Ingest fields
  const [jobInput, setJobInput] = useState('');
  
  // Pipeline result refs
  const [jobId, setJobId] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [optId, setOptId] = useState<string | null>(null);
  const [draftId, setDraftId] = useState<string | null>(null);

  // States
  const [isLoading, setIsLoading] = useState(false);
  const [statusStep, setStatusStep] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleStartPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken || !jobInput.trim()) return;

    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    
    // Simulate steps locally in loader text
    setStatusStep("JOB_PARSING");
    
    try {
      // Step 1: Call API to trigger entire backend orchestrator loop
      const response = await fetch(`${API_BASE_URL}/application/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ job_input: jobInput })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Workflow pipeline execution failed.');
      }

      const data = await response.json();
      
      setJobId(data.job_id);
      setAnalysisId(data.analysis_id);
      setOptId(data.resume_optimization_id);
      setDraftId(data.email_draft_id);

      setSuccessMessage("AI Job understanding and resume tailoring complete! Proceeding to review.");
      
      // Redirect to review page passing reference details
      setTimeout(() => {
        router.push(`/outreach?draft_id=${data.email_draft_id}&job_analysis_id=${data.analysis_id}&resume_optimization_id=${data.resume_optimization_id}`);
      }, 1500);

    } catch (err: any) {
      setErrorMessage(err.message || 'Pipeline failed.');
    } finally {
      setIsLoading(false);
    }
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
            <button className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold">
              Orchestrator Pipeline
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-4xl overflow-y-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white font-sans">
            One-Click Apply Pipeline
          </h1>
          <p className="mt-1 text-slate-400 text-sm">
            Paste a job description, and the AI will parse details, optimize your resume, and draft outreach emails.
          </p>
        </div>

        {successMessage && (
          <div className="p-4 text-sm text-emerald-400 bg-emerald-950 border border-emerald-800 rounded-lg max-w-xl">
            {successMessage}
          </div>
        )}

        {errorMessage && (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-xl">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl max-w-xl space-y-4 shadow-2xl flex flex-col items-center">
            <span className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>
            <div className="text-center">
              <span className="block text-sm font-semibold text-white uppercase tracking-wider">
                Pipeline Stage: {statusStep}
              </span>
              <span className="text-xs text-slate-500">
                Running matching audits and drafting messages...
              </span>
            </div>
          </div>
        ) : (
          <form onSubmit={handleStartPipeline} className="space-y-6 max-w-xl bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">Paste Job Description</label>
              <textarea
                rows={12}
                value={jobInput}
                onChange={(e) => setJobInput(e.target.value)}
                placeholder="Paste the job posting details here to start..."
                className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-600 font-sans leading-relaxed text-sm"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-all shadow-lg"
            >
              Analyze & Tailor in One Click
            </button>
          </form>
        )}
      </main>
    </div>
  );
}
