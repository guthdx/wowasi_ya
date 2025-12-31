import type { NextStep } from '../types';

interface StepCardProps {
  step: NextStep;
  onComplete?: () => void;
  onSkip?: () => void;
  onStartProgress?: () => void;
  isLoading?: boolean;
}

const statusStyles = {
  not_started: 'border-slate/20 bg-white dark:bg-charcoal-light dark:border-slate/30',
  in_progress: 'border-slate bg-slate/10 dark:bg-slate/20 dark:border-slate-light',
  completed: 'border-green-400 bg-green-50 dark:bg-green-900/20 dark:border-green-600',
  skipped: 'border-slate/30 bg-slate/5 dark:bg-charcoal/50 dark:border-slate/30 opacity-60',
};

const statusIcons = {
  not_started: (
    <svg className="w-5 h-5 text-slate/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
    </svg>
  ),
  in_progress: (
    <svg className="w-5 h-5 text-slate animate-spin" fill="none" viewBox="0 0 24 24">
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
    <svg className="w-5 h-5 text-slate/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
    <div className={`border rounded-xl p-4 transition-all ${statusStyles[step.status]}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">{statusIcons[step.status]}</div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-charcoal dark:text-white">{step.title}</h4>
            {step.is_required && (
              <span className="px-1.5 py-0.5 text-xs font-medium bg-terracotta/10 text-terracotta rounded dark:bg-terracotta/20 dark:text-terracotta-light">
                Required
              </span>
            )}
          </div>

          <p className="text-sm text-slate dark:text-slate-light mt-1">{step.description}</p>

          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs px-2 py-0.5 bg-slate/10 rounded text-slate dark:bg-slate/20 dark:text-slate-light">
              {actionTypeLabels[step.action_type]}
            </span>
            {step.completed_at && (
              <span className="text-xs text-slate dark:text-slate-light">
                Completed {new Date(step.completed_at).toLocaleDateString()}
              </span>
            )}
          </div>

          {step.notes && (
            <p className="text-sm text-slate/70 dark:text-slate-light/70 mt-2 italic">Note: {step.notes}</p>
          )}
        </div>

        {canTakeAction && (
          <div className="flex-shrink-0 flex gap-2">
            {step.status === 'not_started' && onStartProgress && (
              <button
                onClick={onStartProgress}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm font-medium text-slate hover:text-slate-dark hover:bg-slate/10 rounded-lg transition-colors disabled:opacity-50 dark:text-slate-light dark:hover:bg-slate/20"
              >
                Start
              </button>
            )}

            {onComplete && (
              <button
                onClick={onComplete}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Complete'}
              </button>
            )}

            {onSkip && step.status !== 'completed' && (
              <button
                onClick={onSkip}
                disabled={isLoading}
                className="px-3 py-1.5 text-sm font-medium text-slate hover:text-charcoal hover:bg-slate/10 rounded-lg transition-colors disabled:opacity-50 dark:text-slate-light dark:hover:bg-slate/20"
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
