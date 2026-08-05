// frontend/src/components/ui/GlassPanel.tsx
import React from 'react';

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  glow?: boolean;
}

export const GlassPanel: React.FC<GlassPanelProps> = ({
  children,
  className = '',
  hoverEffect = false,
  glow = false,
  ...props
}) => {
  return (
    <div
      className={`
        backdrop-blur-xl bg-slate-950/45 
        border border-white/5 rounded-3xl shadow-2xl
        transition-all duration-500 ease-out relative overflow-hidden
        ${hoverEffect ? 'hover:border-white/12 hover:bg-slate-950/55 hover:shadow-indigo-500/5 hover:-translate-y-0.5' : ''}
        ${className}
      `}
      {...props}
    >
      {glow && (
        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 via-transparent to-purple-500/5 pointer-events-none -z-10 blur-xl" />
      )}
      {children}
    </div>
  );
};
