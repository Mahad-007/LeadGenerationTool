// Pipeline Types for managing audit workflow state

export type PipelineStep =
  | 'discovery'
  | 'verification'
  | 'audit'
  | 'analysis'
  | 'contacts'
  | 'outreach'

export type StepStatus = 'idle' | 'pending' | 'running' | 'completed' | 'failed'

export interface StepState {
  status: StepStatus
  progress: number
  message: string
  startedAt?: string
  completedAt?: string
  duration?: number
  itemsProcessed?: number
  error?: string
}

export type PipelineStatus = 'idle' | 'running' | 'paused' | 'completed' | 'failed'

export interface PipelineSummaryData {
  totalDuration: number
  stepsCompleted: number
  totalSteps: number
  sitesProcessed: number
}

export interface PipelineState {
  status: PipelineStatus
  currentStep: PipelineStep | null
  steps: Record<PipelineStep, StepState>
  runId?: string
  startedAt?: string
  completedAt?: string
  summary?: PipelineSummaryData
  error?: string
}

export function isValidPipelineStep(step: string): step is PipelineStep {
  return PIPELINE_STEPS.includes(step as PipelineStep)
}

export interface PipelineConfig {
  niche: string
  maxSites?: number
  skipSteps?: PipelineStep[]
}

export const PIPELINE_STEPS: PipelineStep[] = [
  'discovery',
  'verification',
  'audit',
  'analysis',
  'contacts',
  'outreach',
]

export const STEP_LABELS: Record<PipelineStep, string> = {
  discovery: 'Site Discovery',
  verification: 'Shopify Verification',
  audit: 'Homepage Audit',
  analysis: 'AI Analysis',
  contacts: 'Contact Extraction',
  outreach: 'Email Generation',
}

export function createInitialStepState(): StepState {
  return {
    status: 'idle',
    progress: 0,
    message: '',
  }
}

export function createInitialPipelineState(): PipelineState {
  return {
    status: 'idle',
    currentStep: null,
    steps: {
      discovery: createInitialStepState(),
      verification: createInitialStepState(),
      audit: createInitialStepState(),
      analysis: createInitialStepState(),
      contacts: createInitialStepState(),
      outreach: createInitialStepState(),
    },
  }
}
