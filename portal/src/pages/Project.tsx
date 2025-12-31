import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useNextSteps, useProjectProgress, useCompleteStep, useSkipStep, useUpdateStep } from '../hooks/useNextSteps';
import { ProgressBar } from '../components/ProgressBar';
import { StepCard } from '../components/StepCard';
import { DOCUMENT_PHASES, DOCUMENT_TITLES, type DocumentType } from '../types';

export function Project() {
  const { projectId } = useParams<{ projectId: string }>();
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set(['Phase 1: Foundation']));
  const [selectedDocType] = useState<DocumentType | null>(null);

  const { data: stepsData, isLoading: stepsLoading } = useNextSteps(projectId!, selectedDocType ?? undefined);
  const { data: progress, isLoading: progressLoading } = useProjectProgress(projectId!);

  const completeStep = useCompleteStep(projectId!);
  const skipStep = useSkipStep(projectId!);
  const updateStep = useUpdateStep(projectId!);

  const togglePhase = (phase: string) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(phase)) {
      newExpanded.delete(phase);
    } else {
      newExpanded.add(phase);
    }
    setExpandedPhases(newExpanded);
  };

  const handleComplete = (stepId: string) => {
    completeStep.mutate({ stepId });
  };

  const handleSkip = (stepId: string) => {
    skipStep.mutate({ stepId });
  };

  const handleStartProgress = (stepId: string) => {
    updateStep.mutate({ stepId, updates: { status: 'in_progress' } });
  };

  const getDocTypeProgress = (docType: DocumentType) => {
    const docProgress = progress?.by_document_type[docType];
    if (!docProgress) return 0;
    const done = docProgress.completed + docProgress.skipped;
    return docProgress.total > 0 ? (done / docProgress.total) * 100 : 0;
  };

  const getPhaseProgress = (phaseDocs: readonly DocumentType[]) => {
    if (!progress?.by_document_type) return 0;
    let totalSteps = 0;
    let doneSteps = 0;
    for (const doc of phaseDocs) {
      const dp = progress.by_document_type[doc];
      if (dp) {
        totalSteps += dp.total;
        doneSteps += dp.completed + dp.skipped;
      }
    }
    return totalSteps > 0 ? (doneSteps / totalSteps) * 100 : 0;
  };

  const stepsByDocType = stepsData?.steps.reduce((acc, step) => {
    if (!acc[step.document_type]) {
      acc[step.document_type] = [];
    }
    acc[step.document_type].push(step);
    return acc;
  }, {} as Record<string, typeof stepsData.steps>) ?? {};

  if (stepsLoading || progressLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading project...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 dark:text-gray-400">
        <Link to="/" className="hover:text-gray-700 dark:hover:text-gray-200">
          Dashboard
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900 dark:text-white">Project</span>
      </nav>

      {/* Overall Progress */}
      {progress && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Overall Progress
            </h2>
            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {progress.completion_percentage}%
            </span>
          </div>
          <ProgressBar percentage={progress.completion_percentage} size="lg" showLabel={false} />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Steps</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{progress.total_steps}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Completed</p>
              <p className="text-xl font-semibold text-green-600 dark:text-green-400">{progress.completed_steps}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">In Progress</p>
              <p className="text-xl font-semibold text-blue-600 dark:text-blue-400">{progress.in_progress_steps}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Not Started</p>
              <p className="text-xl font-semibold text-gray-600 dark:text-gray-400">{progress.not_started_steps}</p>
            </div>
          </div>
        </div>
      )}

      {/* Phases */}
      <div className="space-y-4">
        {Object.entries(DOCUMENT_PHASES).map(([phase, docTypes]) => {
          const phaseProgress = getPhaseProgress(docTypes as unknown as DocumentType[]);
          const isExpanded = expandedPhases.has(phase);

          return (
            <div
              key={phase}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              {/* Phase Header */}
              <button
                onClick={() => togglePhase(phase)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span className="font-medium text-gray-900 dark:text-white">{phase}</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    ({docTypes.length} documents)
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <ProgressBar percentage={phaseProgress} size="sm" showLabel={false} />
                  </div>
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {phaseProgress.toFixed(0)}%
                  </span>
                </div>
              </button>

              {/* Phase Content */}
              {isExpanded && (
                <div className="border-t border-gray-200 dark:border-gray-700">
                  {docTypes.map((docType) => {
                    const docProgress = getDocTypeProgress(docType as DocumentType);
                    const docSteps = stepsByDocType[docType] || [];

                    return (
                      <div key={docType} className="border-b last:border-b-0 border-gray-100 dark:border-gray-700/50">
                        {/* Document Header */}
                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50">
                          <div className="flex items-center gap-3">
                            <span className="font-medium text-gray-800 dark:text-gray-200">
                              {DOCUMENT_TITLES[docType as DocumentType]}
                            </span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {docSteps.length} steps
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="w-24">
                              <ProgressBar percentage={docProgress} size="sm" showLabel={false} />
                            </div>
                            <Link
                              to={`/projects/${projectId}/documents/${docType}`}
                              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                            >
                              View →
                            </Link>
                          </div>
                        </div>

                        {/* Steps */}
                        {docSteps.length > 0 && (
                          <div className="p-4 space-y-3">
                            {docSteps.map((step) => (
                              <StepCard
                                key={step.id}
                                step={step}
                                onComplete={() => handleComplete(step.id)}
                                onSkip={() => handleSkip(step.id)}
                                onStartProgress={() => handleStartProgress(step.id)}
                                isLoading={completeStep.isPending || skipStep.isPending || updateStep.isPending}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
