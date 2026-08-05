// frontend/src/features/resume/components/ResumeUploader.tsx
// Component for drag-and-drop master resume file uploads with client validation checks

import React, { useState, useRef } from 'react';

interface ResumeUploaderProps {
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
  errorMessage: string | null;
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({ onUpload, isLoading, errorMessage }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const validTypes = [
      "application/pdf", 
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];
    if (!validTypes.includes(file.type)) {
      alert("Unsupported file format. Please upload a PDF or DOCX document.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("File size exceeds 10MB limit.");
      return;
    }
    setSelectedFile(file);
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      await onUpload(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-xl p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
      <h3 className="mb-4 text-xl font-semibold text-slate-100 font-sans">
        Upload Master Resume
      </h3>
      
      {errorMessage && (
        <div className="p-4 mb-4 text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg">
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
            isDragActive 
              ? "border-indigo-500 bg-indigo-950/10" 
              : "border-slate-700 bg-slate-950 hover:border-slate-600"
          }`}
          onClick={onButtonClick}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleChange}
            accept=".pdf,.docx"
            disabled={isLoading}
          />
          
          <svg
            className="w-12 h-12 mb-4 text-slate-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            ></path>
          </svg>
          
          <p className="mb-2 text-sm text-slate-300">
            <span className="font-semibold text-indigo-400">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-slate-500">PDF or DOCX templates (Max 10MB)</p>
          
          {selectedFile && (
            <div className="mt-4 px-4 py-2 text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 rounded-full">
              Selected: {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
            </div>
          )}
        </div>

        {selectedFile && (
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 transition-all"
          >
            {isLoading ? (
              <span className="flex items-center justify-center space-x-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>Uploading Document...</span>
              </span>
            ) : (
              'Save Master Template'
            )}
          </button>
        )}
      </form>
    </div>
  );
};
