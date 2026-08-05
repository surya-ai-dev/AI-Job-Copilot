// frontend/src/app/jobs/page.tsx
// Next.js page view managing job URL scraping, plain text paste, files upload, & parsed parameters reviews

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

interface JobResponseData {
  id: string;
  source_type: string;
  source_url: string | null;
  company_name: string;
  job_title: string;
  description: string;
  recruiter_email: string | null;
  location: string | null;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function JobsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  const [activeTab, setActiveTab] = useState<'url' | 'text' | 'file' | 'email' | 'whatsapp'>('url');
  
  // Input fields
  const [urlInput, setUrlInput] = useState('');
  const [textInput, setTextInput] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [whatsappMessage, setWhatsappMessage] = useState('');
  const [fileInput, setFileInput] = useState<File | null>(null);

  // States
  const [parsedJob, setParsedJob] = useState<JobResponseData | null>(null);
  const [jobsHistory, setJobsHistory] = useState<JobResponseData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingHistory, setIsFetchingHistory] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadJobsHistory = async () => {
    if (!accessToken) return;
    setIsFetchingHistory(true);
    try {
      const response = await fetch(`${API_BASE_URL}/jobs`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        setJobsHistory(data);
      }
    } catch (err) {
      console.error("Failed to load parsed jobs history:", err);
    } finally {
      setIsFetchingHistory(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    loadJobsHistory();
  }, [isAuthenticated, router]);

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setParsedJob(null);

    try {
      let endpoint = '';
      let headers: Record<string, string> = { 'Authorization': `Bearer ${accessToken}` };
      let body: any = null;

      if (activeTab === 'url') {
        if (!urlInput) throw new Error("URL path cannot be empty.");
        endpoint = '/jobs/parse-url';
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({ url: urlInput });
      } else if (activeTab === 'text') {
        if (!textInput) throw new Error("Job plain text cannot be empty.");
        endpoint = '/jobs/parse-text';
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({ text: textInput });
      } else if (activeTab === 'email') {
        if (!emailBody) throw new Error("Recruiter email body cannot be empty.");
        endpoint = '/jobs/parse-email';
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({ subject: emailSubject || "Opportunity", body: emailBody });
      } else if (activeTab === 'whatsapp') {
        if (!whatsappMessage) throw new Error("WhatsApp message cannot be empty.");
        endpoint = '/jobs/parse-whatsapp';
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({ message: whatsappMessage });
      } else if (activeTab === 'file') {
        if (!fileInput) throw new Error("Please select a file to upload.");
        const isPdf = fileInput.type === "application/pdf";
        endpoint = isPdf ? '/jobs/parse-pdf' : '/jobs/parse-image';
        
        const formData = new FormData();
        formData.append('file', fileInput);
        body = formData;
        // Don't set Content-Type header; browser handles multipart boundary
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Parsing request failed.');
      }

      const jobData = await response.json();
      setParsedJob(jobData);
      
      // Reset inputs
      setUrlInput('');
      setTextInput('');
      setEmailSubject('');
      setEmailBody('');
      setWhatsappMessage('');
      setFileInput(null);

      // Reload log history
      await loadJobsHistory();
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm("Delete this parsed job posting?")) return;
    try {
      const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      if (response.ok) {
        if (parsedJob?.id === jobId) setParsedJob(null);
        await loadJobsHistory();
      }
    } catch (err) {
      console.error("Delete failed:", err);
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
            <button 
              className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold"
            >
              Job Parser Workspace
            </button>
            <button 
              onClick={() => router.push('/profile')}
              className="w-full text-left px-4 py-2.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 font-semibold transition-all"
            >
              Profile Settings
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-5xl overflow-y-auto space-y-12">
        <div>
          <h1 className="text-4xl font-bold text-white font-sans">
            Job Ingestion & Parsing Workspace
          </h1>
          <p className="mt-2 text-slate-400 text-sm">
            Ingest and parse job descriptions from URLs, text, PDFs, screenshots, emails, or WhatsApp messages.
          </p>
        </div>

        {errorMessage && (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-xl">
            {errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start">
          {/* Tabbed Ingest Form */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-slate-800 overflow-x-auto">
              {(['url', 'text', 'file', 'email', 'whatsapp'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider border-b-2 transition-all ${
                    activeTab === tab 
                      ? "border-indigo-500 text-white font-bold" 
                      : "border-transparent text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Ingest Workspace form */}
            <form onSubmit={handleRequestSubmit} className="space-y-4">
              {activeTab === 'url' && (
                <div>
                  <label className="block mb-2 text-sm font-medium text-slate-300">Job Posting Link</label>
                  <input
                    type="url"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://www.linkedin.com/jobs/view/..."
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                </div>
              )}

              {activeTab === 'text' && (
                <div>
                  <label className="block mb-2 text-sm font-medium text-slate-300">Paste Plain JD Text</label>
                  <textarea
                    rows={6}
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Paste the full job description details here..."
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-600 font-sans"
                  />
                </div>
              )}

              {activeTab === 'file' && (
                <div>
                  <label className="block mb-2 text-sm font-medium text-slate-300">Upload Screenshot or PDF JD</label>
                  <input
                    type="file"
                    onChange={(e) => setFileInput(e.target.files?.[0] || null)}
                    accept=".pdf,.png,.jpg,.jpeg"
                    className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300"
                  />
                </div>
              )}

              {activeTab === 'email' && (
                <div className="space-y-4">
                  <div>
                    <label className="block mb-1 text-sm font-medium text-slate-300">Email Subject</label>
                    <input
                      type="text"
                      value={emailSubject}
                      onChange={(e) => setEmailSubject(e.target.value)}
                      placeholder="Opportunity: Senior Python Engineer"
                      className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2"
                    />
                  </div>
                  <div>
                    <label className="block mb-1 text-sm font-medium text-slate-300">Email Body</label>
                    <textarea
                      rows={4}
                      value={emailBody}
                      onChange={(e) => setEmailBody(e.target.value)}
                      placeholder="Hi candidate, we saw your profile..."
                      className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2"
                    />
                  </div>
                </div>
              )}

              {activeTab === 'whatsapp' && (
                <div>
                  <label className="block mb-2 text-sm font-medium text-slate-300">WhatsApp message body</label>
                  <textarea
                    rows={5}
                    value={whatsappMessage}
                    onChange={(e) => setWhatsappMessage(e.target.value)}
                    placeholder="Referral alert: Company X is hiring a lead..."
                    className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-all"
              >
                {isLoading ? "Ingesting & Parsing..." : "Ingest Job Posting"}
              </button>
            </form>
          </div>

          {/* Parsed Output Details Review */}
          {parsedJob && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-6 shadow-2xl">
              <div>
                <span className="px-2.5 py-1 text-xs font-semibold uppercase text-indigo-400 bg-indigo-950/30 border border-indigo-900/50 rounded-full">
                  Source: {parsedJob.source_type}
                </span>
                <h2 className="text-3xl font-bold text-slate-100 font-sans mt-3">
                  {parsedJob.job_title}
                </h2>
                <h4 className="text-xl font-semibold text-slate-400 mt-1">
                  {parsedJob.company_name}
                </h4>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 text-sm text-slate-400">
                <div>
                  <span className="font-semibold text-slate-300">Location:</span> {parsedJob.location || "Not specified"}
                </div>
                <div>
                  <span className="font-semibold text-slate-300">Recruiter Email:</span> {parsedJob.recruiter_email || "Not specified"}
                </div>
              </div>

              <div className="border-t border-slate-800 pt-4">
                <span className="block font-semibold text-slate-300 text-sm mb-2">Requirements Text:</span>
                <p className="text-xs text-slate-400 leading-relaxed max-h-40 overflow-y-auto whitespace-pre-line p-3 bg-slate-950 border border-slate-800 rounded-lg">
                  {parsedJob.description}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* History Listing */}
        <div className="border-t border-slate-800 pt-8">
          <h3 className="text-xl font-bold text-slate-100 mb-4 font-sans">Ingestion History Logs</h3>
          
          {isFetchingHistory ? (
            <div className="text-slate-500">Loading history...</div>
          ) : jobsHistory.length === 0 ? (
            <div className="text-slate-500 text-sm">No parsed jobs logged yet.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {jobsHistory.map((job) => (
                <div key={job.id} className="p-6 bg-slate-900 border border-slate-800 rounded-xl flex justify-between items-start">
                  <div>
                    <span className="text-xs text-slate-500 font-mono uppercase">{job.source_type}</span>
                    <h4 className="font-bold text-slate-100 mt-1">{job.job_title}</h4>
                    <p className="text-sm text-slate-400">{job.company_name}</p>
                  </div>
                  <button
                    onClick={() => handleDeleteJob(job.id)}
                    className="text-xs font-semibold text-red-400 hover:text-red-300 hover:underline"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
