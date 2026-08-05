// frontend/src/app/applications/page.tsx
// Next.js page view showing searchable applications table history and detail cards preview

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

interface JobApplication {
  id: string;
  company_name: string;
  job_title: string;
  job_url: string | null;
  recruiter_email: string | null;
  applied_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function ApplicationsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  const [apps, setApps] = useState<JobApplication[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchApplications = async (query = '') => {
    if (!accessToken) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const url = query.trim()
        ? `${API_BASE_URL}/dashboard/applications/search?query=${encodeURIComponent(query)}`
        : `${API_BASE_URL}/dashboard/applications`;

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });

      if (!response.ok) {
        throw new Error('Failed to retrieve applications.');
      }

      const data = await response.json();
      setApps(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error occurred fetching applications.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchApplications();
  }, [isAuthenticated, router]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchApplications(searchQuery);
  };

  const handleDelete = async (id: string) => {
    if (!accessToken || !window.confirm("Are you sure you want to remove this application log?")) return;
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/applications/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      if (response.ok) {
        setApps(apps.filter((a) => a.id !== id));
      }
    } catch (err) {
      console.error("Failed to delete application log:", err);
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
              onClick={() => router.push('/jobs')}
              className="w-full text-left px-4 py-2.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 font-semibold transition-all"
            >
              Job Parser Workspace
            </button>
            <button className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold">
              Applications List
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-5xl overflow-y-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white font-sans">
              Job Applications Log
            </h1>
            <p className="mt-1 text-slate-400 text-sm">
              Search and filter your applications history.
            </p>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all self-start"
          >
            Back to Dashboard
          </button>
        </div>

        {errorMessage && (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-xl">
            {errorMessage}
          </div>
        )}

        {/* Search bar */}
        <form onSubmit={handleSearchSubmit} className="flex gap-3 max-w-xl">
          <input
            type="text"
            placeholder="Search by company, role or recruiter..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-600 text-sm"
          />
          <button
            type="submit"
            className="px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-all"
          >
            Search
          </button>
        </form>

        {isLoading ? (
          <div className="text-slate-500">Querying application lists...</div>
        ) : apps.length === 0 ? (
          <div className="text-center py-12 text-slate-600 bg-slate-900 border border-slate-800 rounded-2xl p-8">
            No application log logs matching query criteria.
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <table className="w-full text-left text-sm text-slate-400 border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-xs font-semibold uppercase bg-slate-950/40">
                  <th className="py-3 px-6">Company</th>
                  <th className="py-3 px-6">Role</th>
                  <th className="py-3 px-6">Recruiter</th>
                  <th className="py-3 px-6">Applied Date</th>
                  <th className="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((app) => (
                  <tr key={app.id} className="border-b border-slate-800/50 hover:bg-slate-950/20 transition-all">
                    <td className="py-4 px-6 font-semibold text-slate-200">{app.company_name}</td>
                    <td className="py-4 px-6 text-slate-300">{app.job_title}</td>
                    <td className="py-4 px-6 text-slate-500 font-mono text-xs">{app.recruiter_email || "N/A"}</td>
                    <td className="py-4 px-6 text-slate-400">{new Date(app.applied_at).toLocaleDateString()}</td>
                    <td className="py-4 px-6 text-right space-x-2">
                      <button
                        onClick={() => handleDelete(app.id)}
                        className="px-2.5 py-1.5 text-xs text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg hover:bg-red-900/40 transition-all"
                      >
                        Delete Log
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
