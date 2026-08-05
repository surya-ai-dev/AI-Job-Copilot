// frontend/src/app/page.tsx
// Root page routing users directly to login workspace

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to login page on initial load
    router.push('/login');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-400">
      <div className="flex items-center space-x-2">
        <span className="w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></span>
        <span>Loading workspace modules...</span>
      </div>
    </div>
  );
}
