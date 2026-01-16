import { useAnalyticsSummary, useAnalyticsProjects } from '../hooks/useAnalytics';
import type { AnalyticsProject } from '../types';

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs.toFixed(0)}s`;
}

function formatCost(cost: number): string {
  if (cost === 0) return '$0.00';
  if (cost < 0.01) return '<$0.01';
  return `$${cost.toFixed(2)}`;
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function StatCard({
  label,
  value,
  subValue,
  colorClass = 'text-charcoal dark:text-white'
}: {
  label: string;
  value: string | number;
  subValue?: string;
  colorClass?: string;
}) {
  return (
    <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-4">
      <p className="text-sm font-medium text-slate dark:text-slate-light">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${colorClass}`}>{value}</p>
      {subValue && (
        <p className="mt-1 text-xs text-slate/70 dark:text-slate-light/70">{subValue}</p>
      )}
    </div>
  );
}

function ProjectRow({ project }: { project: AnalyticsProject }) {
  const statusColors: Record<string, string> = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    processing: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  };

  return (
    <tr className="border-b border-slate/10 last:border-0">
      <td className="py-3 px-4">
        <div className="font-medium text-charcoal dark:text-white">{project.project_name}</div>
        <div className="text-xs text-slate dark:text-slate-light">
          {new Date(project.timestamp).toLocaleString()}
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[project.status] || statusColors.processing}`}>
          {project.status}
        </span>
      </td>
      <td className="py-3 px-4 text-right text-sm text-charcoal dark:text-white">
        {formatDuration(project.total_duration)}
      </td>
      <td className="py-3 px-4 text-right text-sm text-charcoal dark:text-white">
        {project.documents_generated}
      </td>
      <td className="py-3 px-4 text-right text-sm text-charcoal dark:text-white">
        {formatNumber(project.total_words_generated)}
      </td>
      <td className="py-3 px-4 text-right text-sm text-charcoal dark:text-white">
        {project.generation_provider || '-'}
      </td>
      <td className="py-3 px-4 text-right text-sm text-charcoal dark:text-white">
        {formatCost(project.total_cost_usd)}
      </td>
    </tr>
  );
}

function PhaseTimingBar({
  phases
}: {
  phases: { name: string; duration: number | null; color: string }[]
}) {
  const total = phases.reduce((sum, p) => sum + (p.duration || 0), 0);
  if (total === 0) return <div className="text-sm text-slate">No data</div>;

  return (
    <div className="space-y-2">
      <div className="flex h-6 rounded-lg overflow-hidden">
        {phases.map((phase) => {
          const width = phase.duration ? (phase.duration / total) * 100 : 0;
          if (width < 1) return null;
          return (
            <div
              key={phase.name}
              className={`${phase.color} flex items-center justify-center`}
              style={{ width: `${width}%` }}
              title={`${phase.name}: ${formatDuration(phase.duration)}`}
            >
              {width > 10 && (
                <span className="text-xs font-medium text-white truncate px-1">
                  {phase.name}
                </span>
              )}
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-3 text-xs">
        {phases.map((phase) => (
          <div key={phase.name} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded ${phase.color}`} />
            <span className="text-slate dark:text-slate-light">
              {phase.name}: {formatDuration(phase.duration)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Analytics() {
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useAnalyticsSummary();
  const { data: projects, isLoading: projectsLoading } = useAnalyticsProjects(20);

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate mx-auto"></div>
          <p className="mt-4 text-slate dark:text-slate-light">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (summaryError) {
    return (
      <div className="bg-terracotta/10 dark:bg-terracotta/20 border border-terracotta/30 rounded-xl p-6">
        <h3 className="text-lg font-medium text-terracotta dark:text-terracotta-light">
          Error loading analytics
        </h3>
        <p className="mt-2 text-sm text-terracotta/80 dark:text-terracotta-light/80">
          {summaryError instanceof Error ? summaryError.message : 'An unexpected error occurred'}
        </p>
      </div>
    );
  }

  const phases = summary ? [
    { name: 'Discovery', duration: summary.avg_phase_durations.discovery, color: 'bg-amber-500' },
    { name: 'Research', duration: summary.avg_phase_durations.research, color: 'bg-blue-500' },
    { name: 'Generation', duration: summary.avg_phase_durations.generation, color: 'bg-green-500' },
    { name: 'Quality', duration: summary.avg_phase_durations.quality, color: 'bg-purple-500' },
    { name: 'Output', duration: summary.avg_phase_durations.output, color: 'bg-cyan-500' },
  ] : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-charcoal dark:text-white">Analytics</h1>
        <p className="mt-1 text-slate dark:text-slate-light">
          Usage metrics and performance insights
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard
          label="Total Projects"
          value={summary?.total_projects || 0}
        />
        <StatCard
          label="Success Rate"
          value={`${summary?.success_rate || 0}%`}
          colorClass={summary?.success_rate === 100 ? 'text-green-600 dark:text-green-400' : 'text-charcoal dark:text-white'}
        />
        <StatCard
          label="Avg Duration"
          value={formatDuration(summary?.avg_duration_seconds || null)}
        />
        <StatCard
          label="Total Documents"
          value={formatNumber(summary?.total_documents_generated || 0)}
        />
        <StatCard
          label="Total Words"
          value={formatNumber(summary?.total_words_generated || 0)}
        />
        <StatCard
          label="Total Cost"
          value={formatCost(summary?.total_cost_usd || 0)}
          colorClass="text-green-600 dark:text-green-400"
        />
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-6">
          <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4">
            Project Status
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate dark:text-slate-light">Successful</span>
              <span className="font-semibold text-green-600 dark:text-green-400">
                {summary?.success_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate dark:text-slate-light">Failed</span>
              <span className="font-semibold text-red-600 dark:text-red-400">
                {summary?.failed_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate dark:text-slate-light">Processing</span>
              <span className="font-semibold text-amber-600 dark:text-amber-400">
                {summary?.processing_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-slate/10">
              <span className="text-slate dark:text-slate-light">Unique IPs</span>
              <span className="font-semibold text-charcoal dark:text-white">
                {summary?.unique_ips || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-6">
          <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4">
            Provider Usage
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate dark:text-slate-light">Claude (API)</span>
              <span className="font-semibold text-charcoal dark:text-white">
                {summary?.provider_usage.claude || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate dark:text-slate-light">Llama (Local)</span>
              <span className="font-semibold text-charcoal dark:text-white">
                {summary?.provider_usage.llamacpp || 0}
              </span>
            </div>
            <div className="pt-3 border-t border-slate/10">
              <h3 className="text-sm font-medium text-slate dark:text-slate-light mb-2">
                Output Destinations
              </h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate/70 dark:text-slate-light/70">Filesystem</span>
                  <span>{summary?.output_destinations.filesystem || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate/70 dark:text-slate-light/70">Google Drive</span>
                  <span>{summary?.output_destinations.gdrive || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate/70 dark:text-slate-light/70">Obsidian</span>
                  <span>{summary?.output_destinations.obsidian || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate/70 dark:text-slate-light/70">Outline</span>
                  <span>{summary?.output_destinations.outline || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Average Phase Timing */}
      <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-6">
        <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4">
          Average Phase Duration
        </h2>
        <PhaseTimingBar phases={phases} />
      </div>

      {/* Token Usage */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          label="Research Tokens"
          value={formatNumber(summary?.total_research_tokens || 0)}
          subValue="Total input + output"
        />
        <StatCard
          label="Generation Tokens"
          value={formatNumber(summary?.total_generation_tokens || 0)}
          subValue="Total input + output"
        />
        <StatCard
          label="Total Tokens"
          value={formatNumber(summary?.total_tokens || 0)}
          subValue="All API calls combined"
        />
      </div>

      {/* Recent Projects Table */}
      <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate/10">
          <h2 className="text-lg font-semibold text-charcoal dark:text-white">
            Recent Projects
          </h2>
        </div>

        {projectsLoading ? (
          <div className="p-8 text-center text-slate dark:text-slate-light">
            Loading projects...
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate/5 dark:bg-slate/10">
                <tr>
                  <th className="py-2 px-4 text-left text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Project
                  </th>
                  <th className="py-2 px-4 text-left text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Status
                  </th>
                  <th className="py-2 px-4 text-right text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="py-2 px-4 text-right text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Docs
                  </th>
                  <th className="py-2 px-4 text-right text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Words
                  </th>
                  <th className="py-2 px-4 text-right text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="py-2 px-4 text-right text-xs font-medium text-slate dark:text-slate-light uppercase tracking-wider">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <ProjectRow key={project.project_id} project={project} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-slate dark:text-slate-light">
            No projects tracked yet. Create a project to see analytics.
          </div>
        )}
      </div>
    </div>
  );
}
