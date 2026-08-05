// frontend/src/app/layout.tsx
// Root layout wrapper for the Next.js App Router context

import './globals.css';
import React from 'react';
import QueryProvider from '../providers/QueryProvider';

export const metadata = {
  title: 'AI Job Copilot',
  description: 'AI-powered secure job application assistant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
