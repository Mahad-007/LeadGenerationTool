import { cn } from '@/lib/utils'
import type { PipelineStep, StepState } from '@/types'
import { ProgressBar } from '@/components/shared/ProgressBar'

export interface StepCardProps {
  step: PipelineStep
  label: string
  stepNumber: number
  state: StepState
  isActive: boolean
}

function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000)
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

function getStatusColor(status: StepState['status']): string {
  switch (status) {
    case 'running':
      return 'bg-blue-50 border-blue-200'
    case 'completed':
      return 'bg-green-50 border-green-200'
    case 'failed':
      return 'bg-red-50 border-red-200'
    case 'pending':
      return 'bg-yellow-50 border-yellow-200'
    default:
      return 'bg-gray-50 border-gray-200'
  }
}

function getStatusText(status: StepState['status']): string {
  switch (status) {
    case 'running':
      return 'Running'
    case 'completed':
      return 'Completed'
    case 'failed':
      return 'Failed'
    case 'pending':
      return 'Pending'
    default:
      return 'Waiting'
  }
}

function getStatusBadgeColor(status: StepState['status']): string {
  switch (status) {
    case 'running':
      return 'bg-blue-100 text-blue-700'
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    case 'pending':
      return 'bg-yellow-100 text-yellow-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

export function StepCard({ label, stepNumber, state, isActive }: StepCardProps) {
  const showProgress = state.status === 'running'
  const showCompletedInfo = state.status === 'completed' && (state.duration || state.itemsProcessed)

  return (
    <div
      data-testid="step-card"
      role="region"
      aria-label={`${label} step`}
      className={cn(
        'rounded-lg border p-4 transition-all',
        getStatusColor(state.status),
        isActive && 'ring-2 ring-blue-500'
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">
            Step {stepNumber}
          </p>
          <h3 className="text-sm font-semibold text-gray-900">{label}</h3>
        </div>
        <span
          className={cn(
            'px-2 py-0.5 text-xs font-medium rounded-full',
            getStatusBadgeColor(state.status)
          )}
        >
          {getStatusText(state.status)}
        </span>
      </div>

      {showProgress && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>{state.message}</span>
            <span className="font-medium">{state.progress}%</span>
          </div>
          <ProgressBar
            progress={state.progress}
            variant="default"
            size="sm"
          />
        </div>
      )}

      {showCompletedInfo && (
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-600">
          {state.duration && (
            <span>Duration: {formatDuration(state.duration)}</span>
          )}
          {state.itemsProcessed && (
            <span>{state.itemsProcessed} items processed</span>
          )}
        </div>
      )}

      {state.status === 'failed' && state.error && (
        <div className="mt-3 p-2 bg-red-100 rounded text-xs text-red-700">
          {state.error}
        </div>
      )}
    </div>
  )
}
