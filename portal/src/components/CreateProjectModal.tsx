import { useState, useRef, useCallback } from 'react';
import { useExtractDocument, useCreateProject } from '../hooks/useCreateProject';
import { projectsApi } from '../api/client';
import type { DocumentExtractResult } from '../types';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Step = 'input' | 'preview' | 'creating';

export function CreateProjectModal({ isOpen, onClose }: CreateProjectModalProps) {
  const [step, setStep] = useState<Step>('input');
  const [projectName, setProjectName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [extractedData, setExtractedData] = useState<DocumentExtractResult | null>(null);
  const [manualDescription, setManualDescription] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const extractMutation = useExtractDocument();
  const createMutation = useCreateProject();

  const resetForm = useCallback(() => {
    setStep('input');
    setProjectName('');
    setSelectedFile(null);
    setExtractedData(null);
    setManualDescription('');
    setIsDragOver(false);
    extractMutation.reset();
    createMutation.reset();
  }, [extractMutation, createMutation]);

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['pdf', 'docx', 'txt', 'md'].includes(ext)) {
      return;
    }
    setSelectedFile(file);
    setExtractedData(null);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleExtract = async () => {
    if (!selectedFile) return;

    try {
      const result = await extractMutation.mutateAsync(selectedFile);
      setExtractedData(result);
      setStep('preview');
    } catch {
      // Error is handled by mutation state
    }
  };

  const handleCreate = async () => {
    if (!projectName.trim()) return;

    setStep('creating');

    const description = extractedData?.suggested_description || manualDescription;
    const additionalContext = extractedData?.suggested_additional_context;

    try {
      // Step 1: Create project
      const { project_id } = await createMutation.mutateAsync({
        name: projectName,
        description,
        additional_context: additionalContext || undefined,
      });

      // Step 2: Run discovery (triggers agent matching + privacy scan)
      await projectsApi.getDiscovery(project_id);

      // Step 3: Auto-approve to start generation
      // (We already scanned during document extraction, so we know privacy status)
      await projectsApi.approve(project_id, true, true);

      handleClose();
    } catch {
      setStep(extractedData ? 'preview' : 'input');
    }
  };

  const canProceedFromInput = () => {
    if (!projectName.trim()) return false;
    if (selectedFile) return true;
    return manualDescription.length >= 10;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-charcoal/50 dark:bg-black/70"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate/10 dark:border-slate/20">
          <h2 className="text-xl font-semibold text-charcoal dark:text-white">
            Create New Project
          </h2>
          <p className="text-sm text-slate dark:text-slate/70 mt-1">
            Upload a document or enter details manually
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {step === 'input' && (
            <div className="space-y-6">
              {/* Project Name */}
              <div>
                <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
                  Project Name <span className="text-terracotta">*</span>
                </label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                  className="w-full px-4 py-2 border border-slate/30 dark:border-slate/40 rounded-lg bg-white dark:bg-charcoal focus:outline-none focus:ring-2 focus:ring-slate/50 text-charcoal dark:text-white placeholder:text-slate/50"
                />
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
                  Upload Document <span className="text-slate/50">(optional)</span>
                </label>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    isDragOver
                      ? 'border-slate bg-slate/10'
                      : 'border-slate/30 dark:border-slate/40 hover:border-slate/50'
                  }`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    onChange={handleFileInputChange}
                    className="hidden"
                  />

                  {selectedFile ? (
                    <div>
                      <svg
                        className="mx-auto h-12 w-12 text-green-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      <p className="mt-2 text-sm font-medium text-charcoal dark:text-white">
                        {selectedFile.name}
                      </p>
                      <p className="text-xs text-slate dark:text-slate/70">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFile(null);
                          setExtractedData(null);
                        }}
                        className="mt-2 text-xs text-terracotta hover:underline"
                      >
                        Remove file
                      </button>
                    </div>
                  ) : (
                    <div>
                      <svg
                        className="mx-auto h-12 w-12 text-slate/40"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      <p className="mt-2 text-sm text-slate dark:text-slate/70">
                        Drop a file here or click to browse
                      </p>
                      <p className="text-xs text-slate/50 mt-1">
                        PDF, Word, or TXT (max 10MB)
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Manual Description (when no file) */}
              {!selectedFile && (
                <div>
                  <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
                    Project Description <span className="text-terracotta">*</span>
                  </label>
                  <textarea
                    value={manualDescription}
                    onChange={(e) => setManualDescription(e.target.value)}
                    placeholder="Describe your project in detail. The more context you provide, the better the generated documentation will be..."
                    rows={6}
                    className="w-full px-4 py-2 border border-slate/30 dark:border-slate/40 rounded-lg bg-white dark:bg-charcoal focus:outline-none focus:ring-2 focus:ring-slate/50 text-charcoal dark:text-white resize-none placeholder:text-slate/50"
                  />
                  <p className="text-xs text-slate/50 mt-1">
                    {manualDescription.length.toLocaleString()}/10,000 characters
                  </p>
                </div>
              )}
            </div>
          )}

          {step === 'preview' && extractedData && (
            <div className="space-y-6">
              {/* Extraction Summary */}
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <h3 className="font-medium text-green-800 dark:text-green-400">
                  Document Extracted Successfully
                </h3>
                <ul className="mt-2 text-sm text-green-700 dark:text-green-300 space-y-1">
                  <li>{extractedData.char_count.toLocaleString()} characters extracted</li>
                  {extractedData.page_count && (
                    <li>{extractedData.page_count} pages processed</li>
                  )}
                </ul>
              </div>

              {/* Truncation Warning */}
              {extractedData.was_truncated && (
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                  <h3 className="font-medium text-amber-800 dark:text-amber-400">
                    Text Truncated
                  </h3>
                  <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                    {extractedData.truncation_reason}
                  </p>
                </div>
              )}

              {/* Extraction Warnings */}
              {extractedData.warnings.length > 0 && (
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                  <h3 className="font-medium text-amber-800 dark:text-amber-400">Warnings</h3>
                  <ul className="mt-2 text-sm text-amber-700 dark:text-amber-300 list-disc list-inside">
                    {extractedData.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Privacy Flags */}
              {extractedData.privacy_scan.flags.length > 0 && (
                <div className="bg-terracotta/10 dark:bg-terracotta/20 border border-terracotta/30 rounded-lg p-4">
                  <h3 className="font-medium text-terracotta dark:text-terracotta">
                    Privacy Concerns Detected
                  </h3>
                  <p className="text-sm text-terracotta/80 mt-1">
                    {extractedData.privacy_scan.high_risk_count} high-risk,{' '}
                    {extractedData.privacy_scan.medium_risk_count} medium-risk items found.
                  </p>
                  <p className="text-sm text-terracotta/60 mt-2">
                    These will be reviewed before any external API calls.
                  </p>
                </div>
              )}

              {/* Extracted Text Preview */}
              <div>
                <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
                  Extracted Text Preview
                </label>
                <div className="border border-slate/30 dark:border-slate/40 rounded-lg p-4 max-h-64 overflow-y-auto bg-slate/5 dark:bg-slate/10">
                  <pre className="text-sm text-charcoal dark:text-white whitespace-pre-wrap font-sans">
                    {extractedData.suggested_description.slice(0, 500)}
                    {extractedData.suggested_description.length > 500 && '...'}
                  </pre>
                </div>
                <p className="text-xs text-slate/50 mt-1">
                  Showing first 500 characters of {extractedData.char_count.toLocaleString()} total
                </p>
              </div>
            </div>
          )}

          {step === 'creating' && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate" />
              <p className="mt-4 text-slate dark:text-slate/70">Creating project...</p>
            </div>
          )}
        </div>

        {/* Error Display */}
        {(extractMutation.error || createMutation.error) && (
          <div className="px-6 py-3 bg-terracotta/10 border-t border-terracotta/30">
            <p className="text-sm text-terracotta">
              {(extractMutation.error as Error)?.message ||
                (createMutation.error as Error)?.message ||
                'An error occurred'}
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate/10 dark:border-slate/20 flex justify-end gap-3">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-slate hover:text-charcoal dark:text-slate/70 dark:hover:text-white transition-colors"
          >
            Cancel
          </button>

          {step === 'input' && (
            <>
              {selectedFile ? (
                <button
                  type="button"
                  onClick={handleExtract}
                  disabled={!projectName.trim() || extractMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-white bg-slate hover:bg-slate/80 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {extractMutation.isPending ? 'Extracting...' : 'Extract & Preview'}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleCreate}
                  disabled={!canProceedFromInput() || createMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-white bg-slate hover:bg-slate/80 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Project'}
                </button>
              )}
            </>
          )}

          {step === 'preview' && (
            <>
              <button
                type="button"
                onClick={() => setStep('input')}
                className="px-4 py-2 text-sm font-medium text-slate hover:text-charcoal dark:text-slate/70 dark:hover:text-white transition-colors"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleCreate}
                disabled={createMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-slate hover:bg-slate/80 rounded-lg transition-colors disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating...' : 'Create Project'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
