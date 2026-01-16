import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/client';

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: analyticsApi.getSummary,
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useAnalyticsProjects(limit: number = 50) {
  return useQuery({
    queryKey: ['analytics', 'projects', limit],
    queryFn: () => analyticsApi.getProjects(limit),
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useAnalyticsProject(projectId: string) {
  return useQuery({
    queryKey: ['analytics', 'project', projectId],
    queryFn: () => analyticsApi.getProject(projectId),
    enabled: !!projectId,
  });
}

export function useAnalyticsHealth() {
  return useQuery({
    queryKey: ['analytics', 'health'],
    queryFn: analyticsApi.getHealth,
    staleTime: 1000 * 60, // 1 minute
  });
}
