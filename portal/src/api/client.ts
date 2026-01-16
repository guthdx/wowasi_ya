import axios from 'axios';
import type { AnalyticsProject, AnalyticsSummary, CreateProjectInput, DiscoveryResponse, DocumentExtractResult, NextStep, Project, ProjectProgress } from '../types';

// API configuration from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://wowasi.iyeska.net/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add API key to all requests
api.interceptors.request.use((config) => {
  if (API_KEY) {
    config.headers['X-API-Key'] = API_KEY;
  }
  return config;
});

// Projects API
export const projectsApi = {
  list: async (): Promise<Project[]> => {
    const { data } = await api.get('/projects');
    return data;
  },

  get: async (id: string): Promise<Project> => {
    const { data } = await api.get(`/projects/${id}`);
    return data;
  },

  getStatus: async (id: string) => {
    const { data } = await api.get(`/projects/${id}/status`);
    return data;
  },

  getResult: async (id: string) => {
    const { data } = await api.get(`/projects/${id}/result`);
    return data;
  },

  create: async (input: CreateProjectInput): Promise<{ project_id: string; status: string; message: string }> => {
    const { data } = await api.post('/projects', input);
    return data;
  },

  extractDocument: async (file: File): Promise<DocumentExtractResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post('/extract-document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  getDiscovery: async (id: string): Promise<DiscoveryResponse> => {
    const { data } = await api.get(`/projects/${id}/discovery`);
    return data;
  },

  approve: async (id: string, approved: boolean = true, useSanitized: boolean = true): Promise<{ status: string; message: string }> => {
    const { data } = await api.post(`/projects/${id}/approve`, {
      approved,
      use_sanitized: useSanitized,
    });
    return data;
  },
};

// Next Steps API
export const nextStepsApi = {
  create: async (projectId: string, documentTypes?: string[]) => {
    const { data } = await api.post(`/projects/${projectId}/next-steps`, {
      document_types: documentTypes,
    });
    return data;
  },

  list: async (projectId: string, documentType?: string): Promise<{ steps: NextStep[]; total: number }> => {
    const params = documentType ? { document_type: documentType } : {};
    const { data } = await api.get(`/projects/${projectId}/next-steps`, { params });
    return data;
  },

  get: async (projectId: string, stepId: string): Promise<NextStep> => {
    const { data } = await api.get(`/projects/${projectId}/next-steps/${stepId}`);
    return data;
  },

  update: async (
    projectId: string,
    stepId: string,
    updates: { status?: string; notes?: string; output_data?: Record<string, unknown> }
  ): Promise<NextStep> => {
    const { data } = await api.patch(`/projects/${projectId}/next-steps/${stepId}`, updates);
    return data;
  },

  complete: async (
    projectId: string,
    stepId: string,
    completedBy?: string,
    outputData?: Record<string, unknown>
  ): Promise<NextStep> => {
    const { data } = await api.post(`/projects/${projectId}/next-steps/${stepId}/complete`, {
      completed_by: completedBy,
      output_data: outputData,
    });
    return data;
  },

  skip: async (projectId: string, stepId: string, reason?: string): Promise<NextStep> => {
    const { data } = await api.post(`/projects/${projectId}/next-steps/${stepId}/skip`, {
      reason,
    });
    return data;
  },

  getProgress: async (projectId: string): Promise<ProjectProgress> => {
    const { data } = await api.get(`/projects/${projectId}/progress`);
    return data;
  },
};

// Health check
export const healthApi = {
  check: async () => {
    const { data } = await api.get('/health');
    return data;
  },
};

// Analytics API
export const analyticsApi = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const { data } = await api.get('/analytics/summary');
    return data;
  },

  getProjects: async (limit: number = 50): Promise<AnalyticsProject[]> => {
    const { data } = await api.get('/analytics/projects', { params: { limit } });
    return data;
  },

  getProject: async (projectId: string): Promise<AnalyticsProject> => {
    const { data } = await api.get(`/analytics/projects/${projectId}`);
    return data;
  },

  getHealth: async (): Promise<{ status: string; database: string }> => {
    const { data } = await api.get('/analytics/health');
    return data;
  },
};

export default api;
