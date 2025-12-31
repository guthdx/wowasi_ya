import { useParams, Link } from 'react-router-dom';
import { useNextSteps, useCompleteStep, useSkipStep, useUpdateStep } from '../hooks/useNextSteps';
import { ProgressBar } from '../components/ProgressBar';
import { StepCard } from '../components/StepCard';
import { DOCUMENT_TITLES, type DocumentType } from '../types';

// Outline docs base URL
const OUTLINE_BASE_URL = import.meta.env.VITE_OUTLINE_URL || 'https://docs.iyeska.net';

export function Document() {
  const { projectId, documentType } = useParams<{ projectId: string; documentType: string }>();

  const { data: stepsData, isLoading } = useNextSteps(projectId!, documentType as DocumentType);

  const completeStep = useCompleteStep(projectId!);
  const skipStep = useSkipStep(projectId!);
  const updateStep = useUpdateStep(projectId!);

  const handleComplete = (stepId: string) => {
    completeStep.mutate({ stepId });
  };

  const handleSkip = (stepId: string) => {
    skipStep.mutate({ stepId });
  };

  const handleStartProgress = (stepId: string) => {
    updateStep.mutate({ stepId, updates: { status: 'in_progress' } });
  };

  const title = DOCUMENT_TITLES[documentType as DocumentType] || documentType;

  const completedSteps = stepsData?.steps.filter((s) => s.status === 'completed').length || 0;
  const totalSteps = stepsData?.total || 0;
  const progressPercentage = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate mx-auto"></div>
          <p className="mt-4 text-slate dark:text-slate-light">Loading document...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-slate dark:text-slate-light">
        <Link to="/" className="hover:text-charcoal dark:hover:text-white transition-colors">
          Dashboard
        </Link>
        <span className="mx-2">/</span>
        <Link
          to={`/projects/${projectId}`}
          className="hover:text-charcoal dark:hover:text-white transition-colors"
        >
          Project
        </Link>
        <span className="mx-2">/</span>
        <span className="text-charcoal dark:text-white">{title}</span>
      </nav>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-charcoal dark:text-white">{title}</h1>
          <p className="text-slate dark:text-slate-light mt-1">
            {completedSteps} of {totalSteps} steps complete
          </p>
        </div>
        <a
          href={`${OUTLINE_BASE_URL}/doc/${documentType}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate text-white rounded-lg hover:bg-slate-dark transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
          Open in Outline
        </a>
      </div>

      {/* Progress */}
      <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-charcoal dark:text-white">
            Document Progress
          </span>
          <span className="text-sm font-medium text-slate dark:text-slate-light">
            {progressPercentage.toFixed(0)}%
          </span>
        </div>
        <ProgressBar percentage={progressPercentage} size="md" showLabel={false} />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Embedded Outline */}
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 overflow-hidden">
          <div className="p-4 border-b border-slate/10 dark:border-slate/20">
            <h2 className="font-semibold text-charcoal dark:text-white">Document Preview</h2>
            <p className="text-sm text-slate dark:text-slate-light mt-1">
              View in Outline for full editing capabilities
            </p>
          </div>
          <div className="aspect-[4/3] bg-slate/5 dark:bg-charcoal flex items-center justify-center">
            {/* Placeholder for iframe embed - Outline needs public sharing enabled */}
            <div className="text-center p-8">
              <svg
                className="w-16 h-16 mx-auto text-slate/50"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="mt-4 text-slate dark:text-slate-light">
                Document preview will appear here once Outline public sharing is enabled
              </p>
              <a
                href={`${OUTLINE_BASE_URL}/doc/${documentType}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-4 text-slate hover:text-charcoal dark:text-slate-light dark:hover:text-white transition-colors"
              >
                Open in Outline
              </a>
            </div>
          </div>
        </div>

        {/* Right: Next Steps */}
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 overflow-hidden">
          <div className="p-4 border-b border-slate/10 dark:border-slate/20">
            <h2 className="font-semibold text-charcoal dark:text-white">Next Steps</h2>
            <p className="text-sm text-slate dark:text-slate-light mt-1">
              Actions to take after reviewing this document
            </p>
          </div>
          <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
            {stepsData?.steps.map((step) => (
              <StepCard
                key={step.id}
                step={step}
                onComplete={() => handleComplete(step.id)}
                onSkip={() => handleSkip(step.id)}
                onStartProgress={() => handleStartProgress(step.id)}
                isLoading={completeStep.isPending || skipStep.isPending || updateStep.isPending}
              />
            ))}

            {(!stepsData?.steps || stepsData.steps.length === 0) && (
              <div className="text-center py-8 text-slate dark:text-slate-light">
                <p>No next steps defined for this document</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
