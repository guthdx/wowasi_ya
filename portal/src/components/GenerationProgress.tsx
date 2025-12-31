import { useState, useEffect, useMemo } from 'react';
import type { ProjectStatus } from '../types';

interface GenerationProgressProps {
  status: ProjectStatus;
  currentPhase?: string;
  documentsGenerated?: number;
  totalDocuments?: number;
  startTime?: string;
}

// Quirky status messages like Claude Code
const STATUS_MESSAGES: Record<ProjectStatus, string[]> = {
  agent_discovery: [
    'Discovering project context...',
    'Analyzing domain expertise...',
    'Identifying relevant agents...',
    'Understanding your project...',
    'Mapping knowledge domains...',
  ],
  privacy_review: [
    'Scanning for sensitive data...',
    'Reviewing privacy considerations...',
    'Checking data handling requirements...',
    'Ensuring compliance...',
  ],
  awaiting_approval: [
    'Ready for your review...',
    'Awaiting your go-ahead...',
    'Standing by for approval...',
  ],
  researching: [
    'Researching...',
    'Gathering insights...',
    'Exploring the web...',
    'Finding relevant information...',
    'Diving deep into research...',
    'Consulting sources...',
    'Synthesizing knowledge...',
    'Analyzing market landscape...',
    'Investigating best practices...',
    'Uncovering insights...',
  ],
  generating: [
    'Ideating...',
    'Crafting...',
    'Weaving words...',
    'Assembling documents...',
    'Synthesizing...',
    'Contemplating...',
    'Pondering...',
    'Creating...',
    'Drafting...',
    'Composing...',
    'Building your docs...',
    'Translating ideas...',
    'Articulating concepts...',
    'Shaping content...',
    'Forming structure...',
  ],
  quality_check: [
    'Reviewing quality...',
    'Cross-referencing...',
    'Validating content...',
    'Checking completeness...',
    'Ensuring consistency...',
    'Polishing...',
  ],
  outputting: [
    'Finalizing output...',
    'Writing files...',
    'Organizing documents...',
    'Preparing delivery...',
  ],
  completed: ['All done!', 'Complete!', 'Finished!'],
  failed: ['Something went wrong...'],
};

// Phase descriptions for more detailed progress
const PHASE_DESCRIPTIONS: Record<ProjectStatus, string> = {
  agent_discovery: 'Phase 1 of 5: Agent Discovery',
  privacy_review: 'Phase 2 of 5: Privacy Review',
  awaiting_approval: 'Phase 2 of 5: Awaiting Approval',
  researching: 'Phase 3 of 5: Research',
  generating: 'Phase 4 of 5: Document Generation',
  quality_check: 'Phase 5 of 5: Quality Assurance',
  outputting: 'Phase 5 of 5: Output',
  completed: 'Complete',
  failed: 'Failed',
};

// Visual status for each phase
const PHASE_COLORS: Record<ProjectStatus, { bg: string; text: string; dot: string }> = {
  agent_discovery: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    text: 'text-amber-700 dark:text-amber-400',
    dot: 'bg-amber-500',
  },
  privacy_review: {
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    text: 'text-orange-700 dark:text-orange-400',
    dot: 'bg-orange-500',
  },
  awaiting_approval: {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    text: 'text-purple-700 dark:text-purple-400',
    dot: 'bg-purple-500',
  },
  researching: {
    bg: 'bg-slate/10 dark:bg-slate/20',
    text: 'text-slate dark:text-slate-light',
    dot: 'bg-slate',
  },
  generating: {
    bg: 'bg-slate/10 dark:bg-slate/20',
    text: 'text-slate dark:text-slate-light',
    dot: 'bg-slate',
  },
  quality_check: {
    bg: 'bg-indigo-50 dark:bg-indigo-900/20',
    text: 'text-indigo-700 dark:text-indigo-400',
    dot: 'bg-indigo-500',
  },
  outputting: {
    bg: 'bg-cyan-50 dark:bg-cyan-900/20',
    text: 'text-cyan-700 dark:text-cyan-400',
    dot: 'bg-cyan-500',
  },
  completed: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    text: 'text-green-700 dark:text-green-400',
    dot: 'bg-green-500',
  },
  failed: {
    bg: 'bg-terracotta/10 dark:bg-terracotta/20',
    text: 'text-terracotta dark:text-terracotta-light',
    dot: 'bg-terracotta',
  },
};

export function GenerationProgress({
  status,
  currentPhase,
  documentsGenerated = 0,
  totalDocuments = 15,
  startTime,
}: GenerationProgressProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  const messages = STATUS_MESSAGES[status] || STATUS_MESSAGES.generating;
  const colors = PHASE_COLORS[status];

  // Rotate through quirky messages
  useEffect(() => {
    if (status === 'completed' || status === 'failed') return;

    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [status, messages.length]);

  // Track elapsed time
  useEffect(() => {
    if (!startTime || status === 'completed' || status === 'failed') return;

    const start = new Date(startTime).getTime();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime, status]);

  // Calculate overall progress percentage
  const progressPercent = useMemo(() => {
    const phaseWeights: Record<ProjectStatus, number> = {
      agent_discovery: 5,
      privacy_review: 10,
      awaiting_approval: 10,
      researching: 30,
      generating: 75,
      quality_check: 90,
      outputting: 95,
      completed: 100,
      failed: 0,
    };

    let base = phaseWeights[status];

    // Add document progress within generating phase
    if (status === 'generating' && totalDocuments > 0) {
      const genProgress = (documentsGenerated / totalDocuments) * 45; // 45% of total is generation
      base = 30 + genProgress; // Start at 30% (after research)
    }

    return Math.min(base, 100);
  }, [status, documentsGenerated, totalDocuments]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const isActive = !['completed', 'failed', 'awaiting_approval'].includes(status);

  return (
    <div className={`rounded-xl border ${colors.bg} border-slate/20 overflow-hidden`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isActive && (
              <div className="relative">
                <div className={`w-3 h-3 rounded-full ${colors.dot} animate-pulse-glow`} />
              </div>
            )}
            <div>
              <h3 className={`font-semibold ${colors.text}`}>
                {PHASE_DESCRIPTIONS[status]}
              </h3>
              {currentPhase && (
                <p className="text-sm text-slate/70 dark:text-slate-light/70">
                  {currentPhase}
                </p>
              )}
            </div>
          </div>

          {startTime && (
            <div className="text-right">
              <p className="text-sm font-medium text-charcoal dark:text-white">
                {formatTime(elapsed)}
              </p>
              <p className="text-xs text-slate dark:text-slate-light">elapsed</p>
            </div>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="px-6 py-3 bg-white/50 dark:bg-charcoal/30">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="h-2 bg-slate/20 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ease-out ${colors.dot}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          <span className="text-sm font-medium text-charcoal dark:text-white min-w-[3rem] text-right">
            {progressPercent.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Quirky status message */}
      {isActive && (
        <div className="px-6 py-4 flex items-center justify-center min-h-[60px]">
          <div
            key={messageIndex}
            className="flex items-center gap-3 animate-status-message"
          >
            {/* Animated dots */}
            <div className="flex gap-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${colors.dot} animate-bounce`}
                style={{ animationDelay: '0ms' }}
              />
              <span
                className={`w-1.5 h-1.5 rounded-full ${colors.dot} animate-bounce`}
                style={{ animationDelay: '150ms' }}
              />
              <span
                className={`w-1.5 h-1.5 rounded-full ${colors.dot} animate-bounce`}
                style={{ animationDelay: '300ms' }}
              />
            </div>
            <span className={`text-lg font-medium ${colors.text}`}>
              {messages[messageIndex]}
            </span>
          </div>
        </div>
      )}

      {/* Document progress (during generation) */}
      {status === 'generating' && totalDocuments > 0 && (
        <div className="px-6 py-4 border-t border-slate/10 bg-white/30 dark:bg-charcoal/20">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate dark:text-slate-light">
              Documents generated
            </span>
            <span className="text-sm font-medium text-charcoal dark:text-white">
              {documentsGenerated} of {totalDocuments}
            </span>
          </div>

          {/* Document dots */}
          <div className="mt-3 flex flex-wrap gap-2">
            {Array.from({ length: totalDocuments }).map((_, i) => (
              <div
                key={i}
                className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-medium transition-all duration-300 ${
                  i < documentsGenerated
                    ? 'bg-green-500 text-white'
                    : i === documentsGenerated
                    ? `${colors.dot} text-white animate-pulse`
                    : 'bg-slate/20 text-slate'
                }`}
              >
                {i + 1}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Success state */}
      {status === 'completed' && (
        <div className="px-6 py-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 mb-3">
            <svg
              className="w-6 h-6 text-green-600 dark:text-green-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-green-700 dark:text-green-400">
            Generation Complete!
          </h4>
          <p className="text-sm text-slate dark:text-slate-light mt-1">
            All {totalDocuments} documents have been generated successfully.
          </p>
        </div>
      )}

      {/* Failed state */}
      {status === 'failed' && (
        <div className="px-6 py-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-terracotta/10 dark:bg-terracotta/20 mb-3">
            <svg
              className="w-6 h-6 text-terracotta dark:text-terracotta-light"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-terracotta dark:text-terracotta-light">
            Generation Failed
          </h4>
          <p className="text-sm text-slate dark:text-slate-light mt-1">
            Something went wrong. Please try again or check the logs.
          </p>
        </div>
      )}
    </div>
  );
}
