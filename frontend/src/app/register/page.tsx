// frontend/src/app/register/page.tsx
// Next.js page view displaying the redesigned registration interface
'use client';

import React, { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { RegisterForm } from '../../features/auth/components/RegisterForm';
import { useAuth } from '../../hooks/useAuth';
import { Sparkles, Check, ChevronRight, FileText, Sparkle, Target, ShieldCheck, Briefcase } from 'lucide-react';
import Link from 'next/link';

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isRegistering, registerError } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);

  const handleRegisterSubmit = async (data: any) => {
    try {
      await registerUser(data);
      router.push('/login');
    } catch (err) {
      // Handled internally by react query state hook
    }
  };

  // Mouse follow glow tracker
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      containerRef.current.style.setProperty('--mouse-x', `${x}px`);
      containerRef.current.style.setProperty('--mouse-y', `${y}px`);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      className="mouse-glow-container min-h-screen w-full relative flex flex-col justify-between overflow-x-hidden bg-[#050816] text-slate-100 font-sans select-none"
    >
      {/* Background Interactive Glow */}
      <div className="mouse-glow-bg" />

      {/* Static/Floating Glow Blobs */}
      <div className="absolute top-[-10%] right-[-15%] w-[60%] h-[60%] rounded-full bg-blue-900/10 blur-[150px] -z-10 animate-pulse-glow" />
      <div className="absolute top-[30%] left-[-10%] w-[55%] h-[55%] rounded-full bg-purple-955/20 blur-[180px] -z-10 animate-float" />
      <div className="absolute bottom-[-15%] right-[20%] w-[50%] h-[50%] rounded-full bg-indigo-900/10 blur-[160px] -z-10 animate-float-delayed" />

      {/* Main Responsive Grid */}
      <main className="flex-grow w-full max-w-[1400px] mx-auto px-4 sm:px-6 md:px-8 py-10 md:py-16 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center z-10">
        
        {/* Left Side: Product Hero Area (50% Grid Column Split) */}
        <section className="lg:col-span-6 flex flex-col justify-center space-y-8 lg:pr-8">
          
          {/* Badge */}
          <div className="flex items-center space-x-2 self-start bg-slate-900/40 border border-slate-800/80 px-3.5 py-1.5 rounded-full backdrop-blur-md">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span className="text-xs font-semibold tracking-wide text-indigo-300 uppercase">
              Secure Registration Workspace
            </span>
          </div>

          {/* Heading */}
          <div className="space-y-4">
            <h1 className="text-4xl sm:text-5xl xl:text-6xl font-extrabold tracking-tight leading-none text-gradient-primary">
              Create Your <span className="text-gradient-ai">AI Career Copilot</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-400 leading-relaxed max-w-xl">
              Start optimizing resumes, matching jobs, generating recruiter emails, and preparing for interviews with AI.
            </p>
          </div>

          {/* AI Workflow Node Pipeline */}
          <div className="bg-slate-950/45 border border-slate-900/80 rounded-2xl p-6 backdrop-blur-md shadow-inner shadow-white/5 animate-glow-border border-dashed">
            <h3 className="text-xs font-bold tracking-wider text-slate-500 uppercase mb-4 text-center">
              Onboarding Journey
            </h3>
            
            <div className="relative flex items-center justify-between w-full max-w-lg mx-auto py-2">
              {/* Connector Background Line */}
              <div className="absolute top-1/2 left-4 right-4 h-0.5 bg-slate-900 -translate-y-1/2 z-0" />
              
              {/* Glowing animated line overlay */}
              <div className="absolute top-1/2 left-4 right-4 h-0.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 -translate-y-1/2 z-0 origin-left animate-pulse" />

              {/* Step 1 */}
              <div className="relative z-10 flex flex-col items-center group">
                <div className="w-11 h-11 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center text-blue-400 group-hover:border-blue-500/50 group-hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all duration-300">
                  <FileText className="w-5 h-5" />
                </div>
                <span className="mt-2 text-[10px] sm:text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">Resume</span>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-slate-700 z-10 mt-[-18px]" />

              {/* Step 2 */}
              <div className="relative z-10 flex flex-col items-center group">
                <div className="w-11 h-11 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/50 group-hover:shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all duration-300">
                  <Sparkles className="w-5 h-5" />
                </div>
                <span className="mt-2 text-[10px] sm:text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">AI Analysis</span>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-slate-700 z-10 mt-[-18px]" />

              {/* Step 3 */}
              <div className="relative z-10 flex flex-col items-center group">
                <div className="w-11 h-11 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center text-purple-400 group-hover:border-purple-500/50 group-hover:shadow-[0_0_15px_rgba(168,85,247,0.3)] transition-all duration-300">
                  <Target className="w-5 h-5" />
                </div>
                <span className="mt-2 text-[10px] sm:text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">ATS Opt</span>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-slate-700 z-10 mt-[-18px]" />

              {/* Step 4 */}
              <div className="relative z-10 flex flex-col items-center group">
                <div className="w-11 h-11 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center text-pink-400 group-hover:border-pink-500/50 group-hover:shadow-[0_0_15px_rgba(244,114,182,0.3)] transition-all duration-300">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <span className="mt-2 text-[10px] sm:text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">Interview Ready</span>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-slate-700 z-10 mt-[-18px]" />

              {/* Step 5 */}
              <div className="relative z-10 flex flex-col items-center group">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:border-emerald-500 group-hover:shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all duration-300">
                  <Briefcase className="w-5 h-5" />
                </div>
                <span className="mt-2 text-[10px] sm:text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">Dream Job</span>
              </div>
            </div>
          </div>

          {/* Feature Badges */}
          <div className="flex flex-wrap gap-2.5">
            {[
              'AI Resume Optimization',
              'ATS Score Improvement',
              'Smart Job Matching',
              'AI Email Assistant',
              'Interview Preparation',
            ].map((feature, idx) => (
              <div 
                key={idx}
                className="flex items-center space-x-2 bg-slate-950/45 border border-white/5 hover:border-indigo-500/20 px-3.5 py-2 rounded-xl backdrop-blur-md transition-all duration-300 hover:scale-[1.02] cursor-default"
              >
                <div className="w-4 h-4 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
                  <Check className="w-2.5 h-2.5" />
                </div>
                <span className="text-xs sm:text-sm font-medium text-slate-300">{feature}</span>
              </div>
            ))}
          </div>

          {/* Trust indicators */}
          <div className="grid grid-cols-3 gap-6 pt-6 border-t border-slate-900 text-center sm:text-left">
            <div>
              <div className="text-2xl font-bold text-white tracking-tight">10,000+</div>
              <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wider mt-1">Resumes Optimized</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-indigo-400 tracking-tight">98%</div>
              <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wider mt-1">ATS Accuracy</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-400 tracking-tight">Thousands</div>
              <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wider mt-1">Jobs Parsed</div>
            </div>
          </div>

        </section>

        {/* Right Side: Glassmorphism Register Card (50% Grid Column Split) */}
        <section className="lg:col-span-6 flex justify-center lg:justify-end items-center">
          <RegisterForm
            onSubmit={handleRegisterSubmit}
            isLoading={isRegistering}
            errorMessage={registerError}
          />
        </section>

      </main>

      {/* Simple Footer Links */}
      <footer className="w-full max-w-[1400px] mx-auto px-4 sm:px-6 md:px-8 py-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-600 border-t border-slate-950 z-10 gap-3">
        <div>
          &copy; {new Date().getFullYear()} AI Job Copilot. All rights reserved.
        </div>
        <div className="flex items-center space-x-4">
          <a href="#" className="hover:text-slate-400 transition-colors">Security</a>
          <a href="#" className="hover:text-slate-400 transition-colors">Status</a>
          <a href="#" className="hover:text-slate-400 transition-colors">Contact</a>
        </div>
      </footer>
    </div>
  );
}
