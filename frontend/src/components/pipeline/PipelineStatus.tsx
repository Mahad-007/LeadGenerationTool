import { cn } from '@/lib/utils'
import type { PipelineState } from '@/types'
import { ProgressBar } from '@/components/shared/ProgressBar'

export interface PipelineStatusProps {
  state: PipelineState
  overallProgress: number
  completedSteps: number
  totalSteps: number
}

function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000)
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (remainingSeconds === 0) {
    return `${minutes}m`
  }
  return `${minutes}m ${remainingSeconds}s`
}

function getStatusColor(status: PipelineState['status']): string {
  switch (status) {
    case 'running':
      return 'bg-blue-50 border-blue-200'
    case 'completed':
      return 'bg-green-50 border-green-200'
    case 'failed':
      return 'bg-red-50 border-red-200'
    case 'paused':
      return 'bg-yellow-50 border-yellow-200'
    default:
      return 'bg-gray-50 border-gray-200'
  }
}

function getStatusText(status: PipelineState['status']): string {
  switch (status) {
    case 'running':
      return 'Running'
    case 'completed':
      return 'Completed'
    case 'failed':
      return 'Failed'
    case 'paused':
      return 'Paused'
    default:
      return 'Idle'
  }
}

function getStatusBadgeColor(status: PipelineState['status']): string {
  switch (status) {
    case 'running':
      return 'bg-blue-100 text-blue-700'
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    case 'paused':
      return 'bg-yellow-100 text-yellow-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

function getProgressVariant(status: PipelineState['status']): 'default' | 'success' | 'error' | 'warning' {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    case 'running':
      return 'default'
    default:
      return 'default'
  }
}

export function PipelineStatus({
  state,
  overallProgress,
  completedSteps,
  totalSteps,
}: PipelineStatusProps) {
  const showProgress = state.status !== 'idle'
  const showSummary = state.status === 'completed' && state.summary

  return (
    <div
      role="region"
      aria-label="Pipeline status"
      className={cn(
        'rounded-lg border p-6 transition-all',
        getStatusColor(state.status)
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Pipeline Status</h2>
        <span
          className={cn(
            'px-3 py-1 text-sm font-medium rounded-full',
            getStatusBadgeColor(state.status)
          )}
        >
          {getStatusText(state.status)}
        </span>
      </div>

      <div className="space-y-4">
        {/* Step Progress */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Steps Completed</span>
          <span className="font-medium text-gray-900">
            {completedSteps} / {totalSteps}
          </span>
        </div>

        {/* Progress Bar */}
        {showProgress && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Overall Progress</span>
              <span className="font-medium text-gray-900">
                {Math.round(overallProgress)}%
              </span>
            </div>
            <ProgressBar
              progress={overallProgress}
              variant={getProgressVariant(state.status)}
              size="md"
            />
          </div>
        )}

        {/* Summary Info */}
        {showSummary && (
          <div className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Total Duration</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatDuration(state.summary!.totalDuration)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Sites Processed</p>
              <p className="text-lg font-semibold text-gray-900">
                {state.summary!.sitesProcessed} sites
              </p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {state.status === 'failed' && state.error && (
          <div className="mt-4 p-3 bg-red-100 rounded-md">
            <p className="text-sm text-red-700">{state.error}</p>
          </div>
        )}
      </div>
    </div>
  )
}
