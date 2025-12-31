import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '../api/client';

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  });
}

export function useProjectStatus(id: string) {
  return useQuery({
    queryKey: ['project', id, 'status'],
    queryFn: () => projectsApi.getStatus(id),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll every 5s if project is in progress
      const data = query.state.data;
      if (data && !['completed', 'failed'].includes(data.status)) {
        return 5000;
      }
      return false;
    },
  });
}

export function useProjectResult(id: string) {
  return useQuery({
    queryKey: ['project', id, 'result'],
    queryFn: () => projectsApi.getResult(id),
    enabled: !!id,
  });
}
