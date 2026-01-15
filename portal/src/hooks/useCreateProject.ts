import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../api/client';
import type { CreateProjectInput, DocumentExtractResult } from '../types';

/**
 * Hook for extracting text from uploaded documents.
 * Calls POST /extract-document endpoint.
 */
export function useExtractDocument() {
  return useMutation({
    mutationFn: (file: File): Promise<DocumentExtractResult> => projectsApi.extractDocument(file),
  });
}

/**
 * Hook for creating a new project.
 * Calls POST /projects endpoint.
 * Invalidates projects query on success to refresh the list.
 */
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateProjectInput) => projectsApi.create(input),
    onSuccess: () => {
      // Invalidate and refetch projects list
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
