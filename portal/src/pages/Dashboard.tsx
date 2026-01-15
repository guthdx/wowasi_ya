import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useProjects } from '../hooks/useProjects';
import { ProgressBar } from '../components/ProgressBar';
import { GenerationProgress } from '../components/GenerationProgress';
import { CreateProjectModal } from '../components/CreateProjectModal';
import type { Project, ProjectStatus } from '../types';

const statusLabels: Record<ProjectStatus, string> = {
  agent_discovery: 'Discovering',
  privacy_review: 'Privacy Review',
  awaiting_approval: 'Awaiting Approval',
  researching: 'Researching',
  generating: 'Generating',
  quality_check: 'Quality Check',
  outputting: 'Outputting',
  completed: 'Completed',
  failed: 'Failed',
};

const statusColors: Record<ProjectStatus, string> = {
  agent_discovery: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  privacy_review: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  awaiting_approval: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  researching: 'bg-slate/20 text-slate dark:bg-slate/30 dark:text-slate-light',
  generating: 'bg-slate/20 text-slate dark:bg-slate/30 dark:text-slate-light',
  quality_check: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  outputting: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  failed: 'bg-terracotta/20 text-terracotta dark:bg-terracotta/30 dark:text-terracotta-light',
};

function ProjectCard({ project }: { project: Project }) {
  const isComplete = project.status === 'completed';
  const isInProgress = !['completed', 'failed', 'awaiting_approval'].includes(project.status);

  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-6 hover:shadow-lg hover:border-slate/40 transition-all duration-200"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-charcoal dark:text-white">{project.name}</h3>
          <p className="text-sm text-slate dark:text-slate-light mt-1">
            Created {new Date(project.created_at).toLocaleDateString()}
          </p>
        </div>
        <span
          className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColors[project.status]}`}
        >
          {statusLabels[project.status]}
        </span>
      </div>

      {/* Show mini progress for in-progress projects */}
      {isInProgress && (
        <div className="mt-4 pt-4 border-t border-slate/10">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-slate animate-pulse" />
            </div>
            <span className="text-sm text-slate dark:text-slate-light">
              {statusLabels[project.status]}...
            </span>
          </div>
        </div>
      )}

      {isComplete && (
        <div className="mt-4">
          <ProgressBar percentage={0} size="sm" showLabel={false} />
          <p className="text-xs text-slate dark:text-slate-light mt-1">
            Click to view next steps and progress
          </p>
        </div>
      )}
    </Link>
  );
}

function ActiveProjectCard({ project }: { project: Project }) {
  return (
    <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 overflow-hidden">
      <div className="p-6 border-b border-slate/10">
        <div className="flex items-start justify-between">
          <div>
            <Link
              to={`/projects/${project.id}`}
              className="text-xl font-semibold text-charcoal dark:text-white hover:text-slate transition-colors"
            >
              {project.name}
            </Link>
            <p className="text-sm text-slate dark:text-slate-light mt-1">
              Started {new Date(project.created_at).toLocaleString()}
            </p>
          </div>
          <Link
            to={`/projects/${project.id}`}
            className="text-sm text-slate hover:text-charcoal dark:text-slate-light dark:hover:text-white transition-colors"
          >
            View Details
          </Link>
        </div>
      </div>

      <GenerationProgress
        status={project.status}
        startTime={project.created_at}
        totalDocuments={15}
      />
    </div>
  );
}

export function Dashboard() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { data: projects, isLoading, error } = useProjects();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate mx-auto"></div>
          <p className="mt-4 text-slate dark:text-slate-light">Loading projects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-terracotta/10 dark:bg-terracotta/20 border border-terracotta/30 rounded-xl p-6">
        <h3 className="text-lg font-medium text-terracotta dark:text-terracotta-light">
          Error loading projects
        </h3>
        <p className="mt-2 text-sm text-terracotta/80 dark:text-terracotta-light/80">
          {error instanceof Error ? error.message : 'An unexpected error occurred'}
        </p>
      </div>
    );
  }

  const completedProjects = projects?.filter((p) => p.status === 'completed') || [];
  const activeProjects =
    projects?.filter(
      (p) => !['completed', 'failed', 'awaiting_approval'].includes(p.status)
    ) || [];
  const awaitingProjects = projects?.filter((p) => p.status === 'awaiting_approval') || [];
  const failedProjects = projects?.filter((p) => p.status === 'failed') || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-charcoal dark:text-white">Projects</h1>
          <p className="mt-1 text-slate dark:text-slate-light">
            View and manage your project documentation
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate hover:bg-slate/80 text-white font-medium rounded-lg transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-4">
          <p className="text-sm font-medium text-slate dark:text-slate-light">Total Projects</p>
          <p className="mt-1 text-3xl font-semibold text-charcoal dark:text-white">
            {projects?.length || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-4">
          <p className="text-sm font-medium text-slate dark:text-slate-light">Active</p>
          <p className="mt-1 text-3xl font-semibold text-slate dark:text-slate-light">
            {activeProjects.length}
          </p>
        </div>
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-4">
          <p className="text-sm font-medium text-slate dark:text-slate-light">Completed</p>
          <p className="mt-1 text-3xl font-semibold text-green-600 dark:text-green-400">
            {completedProjects.length}
          </p>
        </div>
        <div className="bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30 p-4">
          <p className="text-sm font-medium text-slate dark:text-slate-light">Awaiting Approval</p>
          <p className="mt-1 text-3xl font-semibold text-purple-600 dark:text-purple-400">
            {awaitingProjects.length}
          </p>
        </div>
      </div>

      {/* Active Projects - Full Progress Display */}
      {activeProjects.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-slate animate-pulse" />
            Currently Generating
          </h2>
          <div className="space-y-4">
            {activeProjects.map((project) => (
              <ActiveProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* Awaiting Approval */}
      {awaitingProjects.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4">
            Awaiting Approval
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {awaitingProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* Completed */}
      {completedProjects.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4">
            Completed Projects
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {completedProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* Failed */}
      {failedProjects.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-charcoal dark:text-white mb-4">Failed</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {failedProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {(!projects || projects.length === 0) && (
        <div className="text-center py-12 bg-white dark:bg-charcoal-light rounded-xl border border-slate/20 dark:border-slate/30">
          <svg
            className="mx-auto h-16 w-16 text-slate/50"
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
          <h3 className="mt-4 text-lg font-medium text-charcoal dark:text-white">No projects yet</h3>
          <p className="mt-2 text-sm text-slate dark:text-slate-light max-w-md mx-auto">
            Create your first project by clicking the button above, or use the CLI.
          </p>
          <div className="mt-6 flex flex-col items-center gap-4">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate hover:bg-slate/80 text-white font-medium rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Project
            </button>
            <span className="text-sm text-slate/50">or use the CLI:</span>
            <code className="px-4 py-2 bg-charcoal/5 dark:bg-white/5 rounded-lg text-sm text-charcoal dark:text-white font-mono">
              wowasi generate "Project Name" "Description..."
            </code>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  );
}
