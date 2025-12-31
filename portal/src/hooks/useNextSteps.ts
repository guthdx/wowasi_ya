import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { nextStepsApi } from '../api/client';
import type { DocumentType } from '../types';

export function useNextSteps(projectId: string, documentType?: DocumentType) {
  return useQuery({
    queryKey: ['nextSteps', projectId, documentType],
    queryFn: () => nextStepsApi.list(projectId, documentType),
    enabled: !!projectId,
  });
}

export function useNextStep(projectId: string, stepId: string) {
  return useQuery({
    queryKey: ['nextStep', projectId, stepId],
    queryFn: () => nextStepsApi.get(projectId, stepId),
    enabled: !!projectId && !!stepId,
  });
}

export function useProjectProgress(projectId: string) {
  return useQuery({
    queryKey: ['progress', projectId],
    queryFn: () => nextStepsApi.getProgress(projectId),
    enabled: !!projectId,
  });
}

export function useCreateNextSteps(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentTypes?: string[]) => nextStepsApi.create(projectId, documentTypes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nextSteps', projectId] });
      queryClient.invalidateQueries({ queryKey: ['progress', projectId] });
    },
  });
}

export function useUpdateStep(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      stepId,
      updates,
    }: {
      stepId: string;
      updates: { status?: string; notes?: string; output_data?: Record<string, unknown> };
    }) => nextStepsApi.update(projectId, stepId, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['nextSteps', projectId] });
      queryClient.invalidateQueries({ queryKey: ['nextStep', projectId, data.id] });
      queryClient.invalidateQueries({ queryKey: ['progress', projectId] });
    },
  });
}

export function useCompleteStep(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      stepId,
      completedBy,
      outputData,
    }: {
      stepId: string;
      completedBy?: string;
      outputData?: Record<string, unknown>;
    }) => nextStepsApi.complete(projectId, stepId, completedBy, outputData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['nextSteps', projectId] });
      queryClient.invalidateQueries({ queryKey: ['nextStep', projectId, data.id] });
      queryClient.invalidateQueries({ queryKey: ['progress', projectId] });
    },
  });
}

export function useSkipStep(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ stepId, reason }: { stepId: string; reason?: string }) =>
      nextStepsApi.skip(projectId, stepId, reason),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['nextSteps', projectId] });
      queryClient.invalidateQueries({ queryKey: ['nextStep', projectId, data.id] });
      queryClient.invalidateQueries({ queryKey: ['progress', projectId] });
    },
  });
}
