// WebSocket Types for real-time communication

export type WebSocketEventType =
  | 'connected'
  | 'pipeline_started'
  | 'step_started'
  | 'step_progress'
  | 'step_completed'
  | 'step_failed'
  | 'pipeline_completed'
  | 'pipeline_failed'

export interface WebSocketConnectedEvent {
  type: 'connected'
  clientId: string
}

export interface WebSocketPipelineStartedEvent {
  type: 'pipeline_started'
  runId: string
  steps: string[]
}

export interface WebSocketStepStartedEvent {
  type: 'step_started'
  step: string
}

export interface WebSocketStepProgressEvent {
  type: 'step_progress'
  step: string
  current: number
  total: number
  percentage: number
  message: string
}

export interface WebSocketStepCompletedEvent {
  type: 'step_completed'
  step: string
  duration: number
  itemsProcessed: number
}

export interface WebSocketStepFailedEvent {
  type: 'step_failed'
  step: string
  error: string
}

export interface WebSocketPipelineCompletedEvent {
  type: 'pipeline_completed'
  summary: PipelineSummary
}

export interface WebSocketPipelineFailedEvent {
  type: 'pipeline_failed'
  error: string
}

export interface PipelineSummary {
  totalDuration: number
  stepsCompleted: number
  totalSteps: number
  sitesProcessed: number
}

export type WebSocketEvent =
  | WebSocketConnectedEvent
  | WebSocketPipelineStartedEvent
  | WebSocketStepStartedEvent
  | WebSocketStepProgressEvent
  | WebSocketStepCompletedEvent
  | WebSocketStepFailedEvent
  | WebSocketPipelineCompletedEvent
  | WebSocketPipelineFailedEvent
