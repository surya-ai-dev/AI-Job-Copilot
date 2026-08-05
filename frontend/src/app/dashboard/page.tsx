// frontend/src/app/dashboard/page.tsx
// Next.js page view displaying aggregate summary metrics and recent applications logs

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

interface RecentApplication {
  id: string;
  company_name: string;
  job_title: string;
  job_url: string | null;
  recruiter_email: string | null;
  applied_at: string;
}

interface SummaryStats {
  total_applications: number;
  applications_today: number;
  active_drafts_count: number;
  recent_resumes_count: number;
  recent_emails_count: number;
  recent_applications: RecentApplication[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);

  const [stats, setStats] = useState<SummaryStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchDashboardStats = async () => {
    if (!accessToken) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/summary`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to retrieve dashboard stats.');
      }

      const data = await response.json();
      setStats(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error occurred querying dashboard.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchDashboardStats();
  }, [isAuthenticated, router]);

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
            <button className="w-full text-left px-4 py-2.5 rounded-lg text-white bg-indigo-600 font-semibold">
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
              onClick={() => router.push('/applications')}
              className="w-full text-left px-4 py-2.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 font-semibold transition-all"
            >
              Applications List
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-5xl overflow-y-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white font-sans">
            Candidate Dashboard
          </h1>
          <p className="mt-1 text-slate-400 text-sm">
            Welcome back! Here is an overview of your job applications history.
          </p>
        </div>

        {errorMessage && (
          <div className="p-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg max-w-xl">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="text-slate-500">Loading summary widgets...</div>
        ) : !stats ? (
          <div className="text-slate-500">No stats metadata retrieved.</div>
        ) : (
          <div className="space-y-8">
            {/* Summary Widget Cards Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {/* Total Applications */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider">Total Apps</span>
                <span className="block mt-2 text-3xl font-black text-white">{stats.total_applications}</span>
              </div>

              {/* Today's Applications */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider">Applied Today</span>
                <span className="block mt-2 text-3xl font-black text-indigo-400">{stats.applications_today}</span>
              </div>

              {/* Resume Versions */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider">Tailored Resumes</span>
                <span className="block mt-2 text-3xl font-black text-white">{stats.recent_resumes_count}</span>
              </div>

              {/* Sent Emails */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
                <span className="block text-slate-500 text-xs font-semibold uppercase tracking-wider">Sent Outreach</span>
                <span className="block mt-2 text-3xl font-black text-emerald-400">{stats.recent_emails_count}</span>
              </div>
            </div>

            {/* Quick Actions Panel */}
            <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex flex-wrap gap-4 items-center justify-between shadow-xl">
              <div>
                <h3 className="font-bold text-slate-100 text-lg">Parser tools shortcuts</h3>
                <p className="text-xs text-slate-500">Jump straight into ingest, optimize, or sending workflows.</p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => router.push('/jobs')}
                  className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-all"
                >
                  Ingest New Job
                </button>
                <button
                  onClick={() => router.push('/resume')}
                  className="px-4 py-2 text-xs font-semibold text-slate-300 bg-slate-950 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all"
                >
                  Upload Master Resume
                </button>
              </div>
            </div>

            {/* Recent Applications table list */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-slate-100 font-sans">Recent Applications Activity</h3>
                <button
                  onClick={() => router.push('/applications')}
                  className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-all"
                >
                  View All Applications →
                </button>
              </div>

              {stats.recent_applications.length === 0 ? (
                <div className="text-center py-8 text-slate-600 text-sm">
                  No applications logged yet. Run job parser and optimizations to begin!
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-400 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-500 text-xs font-semibold uppercase">
                        <th className="py-3 px-4">Company</th>
                        <th className="py-3 px-4">Role</th>
                        <th className="py-3 px-4">Applied Date</th>
                        <th className="py-3 px-4">Recruiter Email</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.recent_applications.map((app) => (
                        <tr key={app.id} className="border-b border-slate-800/50 hover:bg-slate-950/40 transition-all">
                          <td className="py-3.5 px-4 font-semibold text-slate-200">{app.company_name}</td>
                          <td className="py-3.5 px-4 text-slate-300">{app.job_title}</td>
                          <td className="py-3.5 px-4 text-slate-400">
                            {new Date(app.applied_at).toLocaleDateString()}
                          </td>
                          <td className="py-3.5 px-4 text-slate-500 font-mono text-xs">
                            {app.recruiter_email || "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
