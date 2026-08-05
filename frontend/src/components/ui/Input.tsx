// frontend/src/components/ui/Input.tsx
import React, { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: React.ReactNode;
  error?: string;
  rightAction?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, icon, error, rightAction, className = '', type = 'text', ...props }, ref) => {
    return (
      <div className="w-full relative">
        <div className="relative flex items-center group">
          {icon && (
            <div className="absolute left-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors duration-300 pointer-events-none z-10">
              {icon}
            </div>
          )}
          
          <input
            ref={ref}
            type={type}
            className={`
              peer w-full bg-slate-950/60 border rounded-xl text-slate-100 placeholder-transparent
              transition-all duration-300 focus:outline-none 
              focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 focus:shadow-indigo-500/10
              disabled:opacity-50 disabled:cursor-not-allowed z-0
              ${icon ? 'pl-11' : 'pl-4'}
              ${rightAction ? 'pr-12' : 'pr-4'}
              ${error ? 'border-red-500/60 focus:ring-red-500/50 focus:border-red-500' : 'border-slate-800/80 hover:border-slate-700'}
              pt-6 pb-2 text-base h-[58px]
              ${className}
            `}
            placeholder={label}
            {...props}
          />
          
          <label
            className={`
              absolute text-slate-500 pointer-events-none transition-all duration-300 z-10
              peer-placeholder-shown:text-base peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-[16px]
              peer-focus:text-xs peer-focus:text-indigo-400 peer-focus:top-[6px]
              peer-[:not(:placeholder-shown)]:text-indigo-400/80 peer-[:not(:placeholder-shown)]:text-xs peer-[:not(:placeholder-shown)]:top-[6px]
              transform origin-left select-none
              ${icon ? 'left-11' : 'left-4'}
            `}
          >
            {label}
          </label>

          {rightAction && (
            <div className="absolute right-4 text-slate-500 hover:text-slate-300 cursor-pointer z-10 flex items-center justify-center">
              {rightAction}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-400 transition-all duration-200 pl-1">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
export default Input;
