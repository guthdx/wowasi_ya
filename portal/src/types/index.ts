// Project types
export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  created_at: string;
}

export type ProjectStatus =
  | 'agent_discovery'
  | 'privacy_review'
  | 'awaiting_approval'
  | 'researching'
  | 'generating'
  | 'quality_check'
  | 'outputting'
  | 'completed'
  | 'failed';

// Next Steps types
export interface NextStep {
  id: string;
  project_id: string;
  template_id: string;
  document_type: DocumentType;
  title: string;
  description: string;
  action_type: ActionType;
  action_config: Record<string, unknown>;
  is_required: boolean;
  status: StepStatus;
  notes: string | null;
  output_data: Record<string, unknown> | null;
  completed_at: string | null;
  completed_by: string | null;
}

export type DocumentType =
  | 'project_brief'
  | 'readme'
  | 'glossary'
  | 'context_background'
  | 'stakeholder_notes'
  | 'goals_success'
  | 'scope_boundaries'
  | 'timeline_milestones'
  | 'initial_budget'
  | 'risks_assumptions'
  | 'process_workflow'
  | 'sops'
  | 'task_backlog'
  | 'status_updates'
  | 'meeting_notes';

export type ActionType = 'guidance' | 'checklist' | 'form';

export type StepStatus = 'not_started' | 'in_progress' | 'completed' | 'skipped';

// Progress types
export interface ProjectProgress {
  project_id: string;
  total_steps: number;
  completed_steps: number;
  in_progress_steps: number;
  skipped_steps: number;
  not_started_steps: number;
  completion_percentage: number;
  required_steps_total: number;
  required_steps_completed: number;
  by_document_type: Record<string, DocumentTypeProgress>;
}

export interface DocumentTypeProgress {
  total: number;
  completed: number;
  in_progress: number;
  skipped: number;
  not_started: number;
}

// Document phase groupings for UI
export const DOCUMENT_PHASES = {
  'Phase 1: Foundation': [
    'project_brief',
    'readme',
    'glossary',
    'context_background',
    'stakeholder_notes',
  ],
  'Phase 2: Definition': [
    'goals_success',
    'scope_boundaries',
    'timeline_milestones',
    'initial_budget',
    'risks_assumptions',
  ],
  'Phase 3: Operations': [
    'process_workflow',
    'sops',
    'task_backlog',
  ],
  'Phase 4: Communication': [
    'status_updates',
    'meeting_notes',
  ],
} as const;

export const DOCUMENT_TITLES: Record<DocumentType, string> = {
  project_brief: 'Project Brief',
  readme: 'README',
  glossary: 'Glossary',
  context_background: 'Context & Background',
  stakeholder_notes: 'Stakeholder Notes',
  goals_success: 'Goals & Success Criteria',
  scope_boundaries: 'Scope & Boundaries',
  timeline_milestones: 'Timeline & Milestones',
  initial_budget: 'Initial Budget',
  risks_assumptions: 'Risks & Assumptions',
  process_workflow: 'Process Workflow',
  sops: 'SOPs',
  task_backlog: 'Task Backlog',
  status_updates: 'Status Updates',
  meeting_notes: 'Meeting Notes',
};

// Document Upload types
export interface PrivacyFlag {
  data_type: string;
  text: string;
  confidence: number;
  context: string;
}

export interface PrivacyScan {
  original_text: string;
  flags: PrivacyFlag[];
  sanitized_text: string;
  requires_approval: boolean;
  high_risk_count: number;
  medium_risk_count: number;
}

export interface DocumentExtractResult {
  extracted_text: string;
  char_count: number;
  page_count: number | null;
  was_truncated: boolean;
  truncation_reason: string | null;
  warnings: string[];
  privacy_scan: PrivacyScan;
  suggested_description: string;
  suggested_additional_context: string | null;
}

// Project creation types
export interface CreateProjectInput {
  name: string;
  description: string;
  area?: string;
  additional_context?: string;
  output_format?: string;
}
