import type { NextStep } from '../types';

interface StepCardProps {
  step: NextStep;
  onComplete?: () => void;
  onSkip?: () => void;
  onStartProgress?: () => void;
  isLoading?: boolean;
}

const statusStyles = {
  not_started: 'border-gray-200 bg-white dark:bg-gray-800 dark:border-gray-700',
  in_progress: 'border-blue-400 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-600',
  completed: 'border-green-400 bg-green-50 dark:bg-green-900/20 dark:border-green-600',
  skipped: 'border-gray-300 bg-gray-50 dark:bg-gray-800/50 dark:border-gray-600 opacity-60',
};

const statusIcons = {
  not_started: (
    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
    </svg>
  ),
  in_progress: (
    <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  ),
  completed: (
    <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
    </svg>
  ),
  skipped: (
    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
    </svg>
  ),
};

const actionTypeLabels = {
  guidance: 'Read & Review',
  checklist: 'Complete Checklist',
  form: 'Fill Form',
};

export function StepCard({ step, onComplete, onSkip, onStartProgress, isLoading }: StepCardProps) {
  const canTakeAction = step.status === 'not_started' || step.status === 'in_progress';

  return (
    <div className={`border rounded-lg p-4 transition-all ${statusStyles[step.status]}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">{statusIcons[step.status]}</div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-gray-900 dark:text-gray-100">{step.title}</h4>
            {step.is_required && (
              <span className="px-1.5 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded dark:bg-red-900/30 dark:text-red-400">
                Required
              </span>
            )}
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{step.description}</p>

          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs px-2 py-0.5 bg-gray-100 rounded text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              {actionTypeLabels[step.action_type]}
            </span>
            {step.completed_at && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Completed {new Date(step.completed_at).toLocaleDateString()}
              </span>
            )}
          </div>

          {step.notes && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 italic">Note: {step.notes}</p>
          )}
        </div>

        {canTakeAction && (
          <div className="flex-shrink-0 flex gap-2">
            {step.status === 'not_started' && onStartProgress && (
              <button
                onClick={onStartProgress}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors disabled:opacity-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
              >
                Start
              </button>
            )}

            {onComplete && (
              <button
                onClick={onComplete}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Complete'}
              </button>
            )}

            {onSkip && step.status !== 'completed' && (
              <button
                onClick={onSkip}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors disabled:opacity-50 dark:text-gray-400 dark:hover:bg-gray-700"
              >
                Skip
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
