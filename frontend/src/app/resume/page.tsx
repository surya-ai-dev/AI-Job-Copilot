// frontend/src/app/resume/page.tsx
// Next.js page view managing master resume uploads, details review, replacements, & versions list

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';
import { ResumeUploader } from '../../features/resume/components/ResumeUploader';
import { VersionList, ResumeVersionData } from '../../features/resume/components/VersionList';

interface ResumeDetails {
  id: string;
  file_name: string;
  file_size: number;
  content_type: string;
  parsed_skills: string[];
  experience_years: number | null;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function ResumePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  const [resume, setResume] = useState<ResumeDetails | null>(null);
  const [versions, setVersions] = useState<ResumeVersionData[]>([]);
  const [isFetching, setIsFetching] = useState(true);
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch resume details and version history
  const loadResumeData = async () => {
    if (!accessToken) return;
    setIsFetching(true);
    try {
      // 1. Fetch Master Resume Details
      const resumeResponse = await fetch(`${API_BASE_URL}/resume`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });

      if (resumeResponse.ok) {
        const resumeData = await resumeResponse.json();
        setResume(resumeData);
        
        // 2. Fetch version list history
        const versionsResponse = await fetch(`${API_BASE_URL}/resume/versions`, {
          method: 'GET',
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        if (versionsResponse.ok) {
          const versionsData = await versionsResponse.json();
          setVersions(versionsData);
        }
      } else {
        setResume(null);
      }
    } catch (err) {
      console.error("Error loading resume details:", err);
    } finally {
      setIsFetching(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    loadResumeData();
  }, [isAuthenticated, router]);

  const handleUploadSubmit = async (file: File) => {
    setIsLoading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/resume/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to upload resume file.');
      }

      await loadResumeData();
    } catch (err: any) {
      setErrorMessage(err.message || 'Upload failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReplaceSubmit = async (file: File) => {
    setIsLoading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/resume/replace`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to replace resume template.');
      }

      await loadResumeData();
    } catch (err: any) {
      setErrorMessage(err.message || 'Replacement failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadClick = async () => {
    if (!accessToken) return;
    try {
      window.open(`${API_BASE_URL}/resume/download?token=${accessToken}`, '_blank');
    } catch (err) {
      console.error("Download trigger failed:", err);
    }
  };

  const handleDeleteClick = async () => {
    if (!confirm("Are you sure you want to delete your master resume template? This will delete all physical files.")) return;
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/resume`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      if (response.ok) {
        setResume(null);
        setVersions([]);
      } else {
        const errData = await response.json();
        alert(errData.detail || "Deletion failed.");
      }
    } catch (err) {
      console.error("Delete failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadVersion = async (versionId: string) => {
    // Version download simulation for MVP
    alert(`Downloading version ID: ${versionId}`);
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
              className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold"
            >
              Resume Workspace
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
            Resume Workspace
          </h1>
          <p className="mt-2 text-slate-400 text-sm">
            Upload, replace, and track optimized versions of your professional resume template.
          </p>
        </div>

        {isFetching ? (
          <div className="flex items-center space-x-2 text-slate-500">
            <span className="w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></span>
            <span>Retrieving profile files details...</span>
          </div>
        ) : !resume ? (
          /* Upload State */
          <div className="space-y-6">
            <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl max-w-xl">
              <h3 className="text-lg font-semibold text-slate-100 mb-2">No master resume uploaded</h3>
              <p className="text-sm text-slate-400">
                You must upload a master resume template (PDF or DOCX) to begin using the Copilot. The original template is kept immutable.
              </p>
            </div>
            <ResumeUploader
              onUpload={handleUploadSubmit}
              isLoading={isLoading}
              errorMessage={errorMessage}
            />
          </div>
        ) : (
          /* Details Dashboard & Versions */
          <div className="space-y-10">
            {/* Master Resume Details Card */}
            <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6 max-w-3xl">
              <div className="space-y-4">
                <div className="space-y-1">
                  <h2 className="text-2xl font-bold text-slate-100 font-sans">
                    {resume.file_name}
                  </h2>
                  <p className="text-xs text-slate-500">
                    Uploaded: {new Date(resume.created_at).toLocaleString()} • Size: {(resume.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 pt-2">
                  {resume.parsed_skills.map((skill, index) => (
                    <span 
                      key={index} 
                      className="px-2.5 py-1 text-xs font-semibold text-indigo-400 bg-indigo-950/30 border border-indigo-900/50 rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 md:self-start">
                <button
                  onClick={handleDownloadClick}
                  className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-all"
                >
                  Download Template
                </button>
                <button
                  onClick={handleDeleteClick}
                  className="px-4 py-2 text-sm font-semibold text-red-400 bg-red-950/20 border border-red-900/50 rounded-lg hover:bg-red-900/40 transition-all"
                  disabled={isLoading}
                >
                  Delete
                </button>
              </div>
            </div>

            {/* Replace Form Dropdown */}
            <div className="max-w-xl border-t border-slate-800 pt-8">
              <h4 className="text-md font-semibold text-slate-300 mb-4">Replace Master Template</h4>
              <ResumeUploader
                onUpload={handleReplaceSubmit}
                isLoading={isLoading}
                errorMessage={errorMessage}
              />
            </div>

            {/* Versions Listing */}
            <div className="border-t border-slate-800 pt-8">
              <VersionList
                versions={versions}
                onDownloadVersion={handleDownloadVersion}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
