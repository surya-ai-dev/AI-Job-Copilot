// frontend/src/features/resume/components/VersionList.tsx
// Component displaying the list of tailored resume versions and metadata details

import React from 'react';

export interface ResumeVersionData {
  id: string;
  resume_id: string;
  version_number: number;
  file_path: string;
  optimized_for_company: string;
  optimized_for_role: string;
  created_at: string;
}

interface VersionListProps {
  versions: ResumeVersionData[];
  onDownloadVersion: (versionId: string) => Promise<void>;
}

export const VersionList: React.FC<VersionListProps> = ({ versions, onDownloadVersion }) => {
  if (versions.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 bg-slate-900/50 border border-slate-800 rounded-xl">
        No tailored versions generated yet. These will be tracked here once you optimization resumes for target jobs.
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="p-6 border-b border-slate-800">
        <h3 className="text-lg font-semibold text-slate-100 font-sans">
          Tailored Resume Versions History
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-slate-300">
          <thead className="bg-slate-950 text-slate-400 text-xs font-semibold uppercase">
            <tr>
              <th className="px-6 py-4">Version</th>
              <th className="px-6 py-4">Target Company</th>
              <th className="px-6 py-4">Target Role</th>
              <th className="px-6 py-4">Generated Date</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-sm">
            {versions.map((version) => (
              <tr key={version.id} className="hover:bg-slate-800/30 transition-all">
                <td className="px-6 py-4 font-mono font-medium text-slate-400">
                  v{version.version_number}
                </td>
                <td className="px-6 py-4 font-semibold text-slate-100">
                  {version.optimized_for_company}
                </td>
                <td className="px-6 py-4">
                  {version.optimized_for_role}
                </td>
                <td className="px-6 py-4 text-slate-500">
                  {new Date(version.created_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => onDownloadVersion(version.id)}
                    className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-all"
                  >
                    Download PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
