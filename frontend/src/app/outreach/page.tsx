// frontend/src/app/outreach/page.tsx
// Next.js page view managing recruiter outreach email drafts, Gmail API scopes, and deliveries reviews

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

interface EmailDraftData {
  id: string;
  recipient_email: string;
  recipient_name: string | null;
  subject: string;
  body: string;
  attachment_path: string | null;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function OutreachPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const job_analysis_id = searchParams.get('job_analysis_id');
  const resume_optimization_id = searchParams.get('resume_optimization_id');
  const active_draft_id = searchParams.get('draft_id');

  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  // Form Fields
  const [recipientEmail, setRecipientEmail] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  
  // States
  const [draftId, setDraftId] = useState<string | null>(null);
  const [attachmentName, setAttachmentName] = useState<string | null>(null);
  
  const [gmailConnected, setGmailConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const checkGmailOAuthStatus = async () => {
    if (!accessToken) return;
    try {
      const response = await fetch(`${API_BASE_URL}/email/oauth/status`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGmailConnected(data.connected);
      }
    } catch (err) {
      console.error("Failed to query Gmail status:", err);
    }
  };

  const loadOrCreateDraft = async () => {
    if (!accessToken) return;
    setIsLoading(true);
    setErrorMessage(null);

    try {
      if (active_draft_id) {
        // Load existing draft
        const response = await fetch(`${API_BASE_URL}/email/drafts`, {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        if (response.ok) {
          const drafts = await response.json();
          const target = drafts.find((d: any) => d.id === active_draft_id);
          if (target) {
            populateForm(target);
            setIsLoading(false);
            return;
          }
        }
      }

      if (job_analysis_id && resume_optimization_id) {
        // Generate new draft
        const response = await fetch(`${API_BASE_URL}/email/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          },
          body: JSON.stringify({ job_analysis_id, resume_optimization_id })
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Outreach email generation failed.');
        }

        const data = await response.json();
        populateForm(data);
      } else {
        throw new Error("Missing job analysis or resume reference.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to initialize draft.');
    } finally {
      setIsLoading(false);
    }
  };

  const populateForm = (draft: EmailDraftData) => {
    setDraftId(draft.id);
    setRecipientEmail(draft.recipient_email);
    setRecipientName(draft.recipient_name || '');
    setSubject(draft.subject);
    setBody(draft.body);
    if (draft.attachment_path) {
      const parts = draft.attachment_path.split(/[/\\]/);
      setAttachmentName(parts[parts.length - 1]);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    checkGmailOAuthStatus();
    loadOrCreateDraft();
  }, [isAuthenticated, job_analysis_id, resume_optimization_id, active_draft_id, router]);

  const handleSaveDraft = async () => {
    if (!accessToken || !draftId) return;
    setIsLoading(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/email/draft/${draftId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          recipient_email: recipientEmail,
          recipient_name: recipientName || null,
          subject,
          body
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to save draft changes.');
      }

      setSuccessMessage("Outreach email draft saved successfully.");
    } catch (err: any) {
      setErrorMessage(err.message || 'Save draft failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendEmail = async () => {
    if (!accessToken || !draftId) return;
    if (!gmailConnected) {
      alert("Please connect your Gmail account via OAuth before sending.");
      return;
    }
    
    setIsSending(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      // First save active changes
      await handleSaveDraft();

      const response = await fetch(`${API_BASE_URL}/email/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ draft_id: draftId })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to deliver email.');
      }

      setSuccessMessage("Outreach email sent successfully via Gmail API!");
      setTimeout(() => router.push('/dashboard'), 2000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Delivery failed.');
    } finally {
      setIsSending(false);
    }
  };

  const triggerGmailOAuthConnect = () => {
    // Mocks OAuth redirect hook callback locally
    const access_token = "mock_gmail_oauth_token_holder_123";
    const expires_in = 3600; // 1 hour
    window.location.href = `${window.location.pathname}?job_analysis_id=${job_analysis_id}&resume_optimization_id=${resume_optimization_id}&oauth_mock=success`;
    
    // Call token registrar endpoint (mimicking server OAuth flow)
    fetch(`${API_BASE_URL}/email/oauth/callback?access_token=${access_token}&expires_in=${expires_in}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }).then(() => checkGmailOAuthStatus());
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
              Outreach Workspace
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-4xl overflow-y-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white font-sans">
              Outreach Composer Workspace
            </h1>
            <p className="mt-1 text-slate-400 text-sm">
              Review, edit, and approve recruiter outreach emails before delivery.
            </p>
          </div>
          
          {/* Gmail OAuth connection status */}
          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 self-start sm:self-center">
            <span className={`w-2.5 h-2.5 rounded-full ${gmailConnected ? "bg-emerald-500" : "bg-amber-500"}`}></span>
            <span className="text-xs text-slate-300 font-semibold">
              Gmail {gmailConnected ? "Connected" : "Not Authorized"}
            </span>
            {!gmailConnected && (
              <button
                onClick={triggerGmailOAuthConnect}
                className="ml-2 px-2.5 py-1 text-[10px] font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-all"
              >
                Connect OAuth
              </button>
            )}
          </div>
        </div>

        {successMessage && (
          <div className="p-4 text-sm text-emerald-400 bg-emerald-950 border border-emerald-800 rounded-lg max-w-2xl animate-fade-in">
            {successMessage}
          </div>
        )}

        {errorMessage && (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-2xl">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="text-slate-500">Loading composer template details...</div>
        ) : (
          <form className="space-y-6 max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
            {/* Recipient */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 text-sm font-medium text-slate-300">Recruiter Name</label>
                <input
                  type="text"
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium text-slate-300">Recruiter Email</label>
                <input
                  type="email"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                  required
                />
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">Email Subject Line</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-600 font-semibold"
                required
              />
            </div>

            {/* Body */}
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">Personalized Body Content</label>
              <textarea
                rows={10}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="w-full px-4 py-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-600 font-sans leading-relaxed text-sm"
                required
              />
            </div>

            {/* Attachment Preview */}
            {attachmentName && (
              <div className="border-t border-slate-800 pt-4 flex items-center justify-between bg-slate-950 border border-slate-800 rounded-xl px-4 py-3">
                <div className="flex items-center gap-3">
                  <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path>
                  </svg>
                  <div>
                    <span className="block text-sm font-medium text-slate-200">{attachmentName}</span>
                    <span className="text-slate-500 text-xs">PDF Document attached</span>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-4 justify-between border-t border-slate-800 pt-6">
              <button
                type="button"
                onClick={() => router.push('/resume')}
                className="px-6 py-2.5 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all"
              >
                Cancel
              </button>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleSaveDraft}
                  className="px-6 py-2.5 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all"
                >
                  Save Draft
                </button>
                <button
                  type="button"
                  onClick={handleSendEmail}
                  disabled={isSending}
                  className="px-8 py-2.5 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-all"
                >
                  {isSending ? "Delivering..." : "Send Email"}
                </button>
              </div>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}
