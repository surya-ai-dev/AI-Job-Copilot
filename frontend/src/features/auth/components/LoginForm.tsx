// frontend/src/features/auth/components/LoginForm.tsx
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles } from 'lucide-react';
import { Input } from '../../../components/ui/Input';
import { Button } from '../../../components/ui/Button';
import { GlassPanel } from '../../../components/ui/GlassPanel';
import Link from 'next/link';

const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email address." }),
  password: z.string().min(8, { message: "Password must be at least 8 characters long." }),
});

type LoginFields = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSubmit: (data: LoginFields) => Promise<void>;
  isLoading: boolean;
  errorMessage: string | null;
}

const GoogleIcon = () => (
  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.85z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.85c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

const LinkedInIcon = () => (
  <svg className="w-5 h-5 mr-2 text-[#0A66C2]" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
  </svg>
);

const GitHubIcon = () => (
  <svg className="w-5 h-5 mr-2 text-white" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
  </svg>
);

export const LoginForm: React.FC<LoginFormProps> = ({ onSubmit, isLoading, errorMessage }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFields>({
    resolver: zodResolver(loginSchema),
  });

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <GlassPanel className="w-full max-w-[480px] p-8 md:p-10 shadow-2xl relative animate-glow-border border" glow={true}>
      {/* Top Header & Logo */}
      <div className="flex flex-col items-center mb-8 text-center">
        <div className="flex items-center justify-center w-12 h-12 mb-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
          <Sparkles className="w-6 h-6 animate-pulse" />
        </div>
        <div className="flex items-center space-x-2">
          <h2 className="text-xl font-bold tracking-tight text-white">
            AI Job Copilot
          </h2>
          <span className="px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase rounded-full text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 glow-badge">
            Powered by AI
          </span>
        </div>
        <div className="mt-3">
          <h3 className="text-2xl font-semibold text-slate-100">Welcome Back 👋</h3>
          <p className="mt-1.5 text-sm text-slate-400">
            Continue building your career with AI.
          </p>
        </div>
      </div>

      {/* API Error Messages */}
      {errorMessage && (
        <div className="p-4 mb-6 text-sm text-red-400 bg-red-950/40 border border-red-500/20 rounded-xl flex items-start space-x-2 animate-pulse">
          <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Form Submission */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <Input
          label="Email Address"
          type="email"
          disabled={isLoading}
          error={errors.email?.message}
          icon={<Mail className="w-5 h-5" />}
          {...register('email')}
        />

        <Input
          label="Password"
          type={showPassword ? 'text' : 'password'}
          disabled={isLoading}
          error={errors.password?.message}
          icon={<Lock className="w-5 h-5" />}
          rightAction={
            <button
              type="button"
              onClick={togglePasswordVisibility}
              tabIndex={-1}
              className="text-slate-500 hover:text-slate-300 focus:outline-none transition-colors p-1"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          }
          {...register('password')}
        />

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between text-sm py-1 select-none">
          <label className="flex items-center space-x-2 cursor-pointer group text-slate-400 hover:text-slate-300 transition-colors">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded border-slate-800 bg-slate-950/60 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-slate-950 focus:ring-offset-2 transition-all cursor-pointer"
            />
            <span>Remember Me</span>
          </label>

          <Link
            href="/forgot-password"
            className="text-indigo-400 hover:text-indigo-300 hover:underline font-medium transition-colors"
          >
            Forgot Password?
          </Link>
        </div>

        {/* Action Button */}
        <Button
          type="submit"
          isLoading={isLoading}
          className="group mt-2"
          rightIcon={<ArrowRight className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" />}
        >
          {isLoading ? 'Preparing your workspace...' : 'Sign In'}
        </Button>
      </form>

      {/* OR Divider */}
      <div className="relative my-7 flex items-center justify-center">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-800/80"></div>
        </div>
        <span className="relative px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-950/5 py-1 rounded-full backdrop-blur-md border border-slate-800/20">
          Continue with
        </span>
      </div>

      {/* Social Logins */}
      <div className="grid grid-cols-3 gap-3">
        <button
          type="button"
          className="flex items-center justify-center py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300 hover:-translate-y-0.5 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          aria-label="Continue with Google"
        >
          <GoogleIcon />
        </button>
        <button
          type="button"
          className="flex items-center justify-center py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300 hover:-translate-y-0.5 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          aria-label="Continue with LinkedIn"
        >
          <LinkedInIcon />
        </button>
        <button
          type="button"
          className="flex items-center justify-center py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300 hover:-translate-y-0.5 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          aria-label="Continue with GitHub"
        >
          <GitHubIcon />
        </button>
      </div>

      {/* Footer Links */}
      <div className="mt-8 text-center text-sm text-slate-500">
        Don&apos;t have an account?{' '}
        <Link href="/register" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-all hover:underline">
          Create Account
        </Link>
        <div className="flex items-center justify-center space-x-3 mt-4 text-xs text-slate-600 border-t border-slate-800/50 pt-4">
          <Link href="/terms" className="hover:text-slate-400 transition-colors">Terms of Service</Link>
          <span>•</span>
          <Link href="/privacy" className="hover:text-slate-400 transition-colors">Privacy Policy</Link>
          <span>•</span>
          <Link href="/support" className="hover:text-slate-400 transition-colors">Support</Link>
        </div>
      </div>
    </GlassPanel>
  );
};
