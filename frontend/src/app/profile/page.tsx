// frontend/src/app/profile/page.tsx
// Profile view page allowing users to review and update account profiles

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

const profileSchema = z.object({
  first_name: z.string().min(1, { message: "First name is required." }),
  last_name: z.string().min(1, { message: "Last name is required." }),
});

type ProfileFields = z.infer<typeof profileSchema>;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function ProfilePage() {
  const router = useRouter();
  const { logout, user, isAuthenticated } = useAuth();
  const accessToken = useAuthStore((state) => state.accessToken);
  const updateUser = useAuthStore((state) => state.updateUser);
  
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ProfileFields>({
    resolver: zodResolver(profileSchema),
  });

  // Load user profile details on mount
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (user) {
      setValue('first_name', user.first_name);
      setValue('last_name', user.last_name);
    }
  }, [user, isAuthenticated, router, setValue]);

  const onSubmit = async (data: ProfileFields) => {
    setIsLoading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to update profile settings.');
      }

      const updatedUser = await response.json();
      updateUser(updatedUser.first_name, updatedUser.last_name);
      setSuccessMessage('Profile details updated successfully!');
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred during save.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogoutClick = async () => {
    await logout();
    router.push('/login');
  };

  if (!isAuthenticated) {
    return null; // Route protection handles redirect
  }

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
              Profile Settings
            </button>
          </nav>
        </div>
        <div>
          <button 
            onClick={handleLogoutClick}
            className="w-full text-left px-4 py-2.5 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-950/20 font-semibold transition-all"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 p-8 md:p-16 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8 text-white font-sans">
          Profile Settings
        </h1>

        {successMessage && (
          <div className="p-4 mb-6 text-sm text-emerald-400 bg-emerald-950 border border-emerald-800 rounded-lg">
            {successMessage}
          </div>
        )}

        {errorMessage && (
          <div className="p-4 mb-6 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-xl">
          <div>
            <label className="block mb-2 text-sm font-medium text-slate-300">
              Email Address (Read-Only)
            </label>
            <input
              type="email"
              value={user?.email || ''}
              className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 cursor-not-allowed focus:outline-none"
              disabled
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">
                First Name
              </label>
              <input
                type="text"
                {...register('first_name')}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                disabled={isLoading}
              />
              {errors.first_name && (
                <p className="mt-1 text-xs text-red-500">{errors.first_name.message}</p>
              )}
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-slate-300">
                Last Name
              </label>
              <input
                type="text"
                {...register('last_name')}
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                disabled={isLoading}
              />
              {errors.last_name && (
                <p className="mt-1 text-xs text-red-500">{errors.last_name.message}</p>
              )}
            </div>
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 transition-all"
            >
              {isLoading ? 'Saving Changes...' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={() => router.push('/dashboard')}
              className="px-6 py-2.5 text-sm font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 focus:outline-none transition-all"
            >
              Back to Dashboard
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
