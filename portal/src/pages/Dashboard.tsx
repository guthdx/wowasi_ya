import { Link } from 'react-router-dom';
import { useProjects } from '../hooks/useProjects';
import { ProgressBar } from '../components/ProgressBar';
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
  agent_discovery: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  privacy_review: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  awaiting_approval: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  researching: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  generating: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  quality_check: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  outputting: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

function ProjectCard({ project }: { project: Project }) {
  const isComplete = project.status === 'completed';

  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{project.name}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Created {new Date(project.created_at).toLocaleDateString()}
          </p>
        </div>
        <span
          className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColors[project.status]}`}
        >
          {statusLabels[project.status]}
        </span>
      </div>

      {isComplete && (
        <div className="mt-4">
          <ProgressBar percentage={0} size="sm" showLabel={false} />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Click to view next steps and progress
          </p>
        </div>
      )}
    </Link>
  );
}

export function Dashboard() {
  const { data: projects, isLoading, error } = useProjects();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading projects...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-red-800 dark:text-red-400">Error loading projects</h3>
        <p className="mt-2 text-sm text-red-700 dark:text-red-300">
          {error instanceof Error ? error.message : 'An unexpected error occurred'}
        </p>
      </div>
    );
  }

  const completedProjects = projects?.filter((p) => p.status === 'completed') || [];
  const inProgressProjects = projects?.filter((p) => p.status !== 'completed' && p.status !== 'failed') || [];
  const failedProjects = projects?.filter((p) => p.status === 'failed') || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Projects</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          View and manage your project documentation
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Projects</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
            {projects?.length || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Completed</p>
          <p className="mt-1 text-3xl font-semibold text-green-600 dark:text-green-400">
            {completedProjects.length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">In Progress</p>
          <p className="mt-1 text-3xl font-semibold text-blue-600 dark:text-blue-400">
            {inProgressProjects.length}
          </p>
        </div>
      </div>

      {/* In Progress */}
      {inProgressProjects.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">In Progress</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {inProgressProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* Completed */}
      {completedProjects.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
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
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Failed</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {failedProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {(!projects || projects.length === 0) && (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
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
          <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No projects yet</h3>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Use the Wowasi Ya CLI or API to generate your first project.
          </p>
        </div>
      )}
    </div>
  );
}
