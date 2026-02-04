import { cn } from '@/lib/utils'
import type { PipelineStatus } from '@/types'

export interface HeaderProps {
  pipelineStatus: PipelineStatus
  onRunPipeline: () => void
  onStopPipeline: () => void
}

function getStatusBadgeColor(status: PipelineStatus): string {
  switch (status) {
    case 'running':
      return 'bg-blue-100 text-blue-700 border-blue-200'
    case 'completed':
      return 'bg-green-100 text-green-700 border-green-200'
    case 'failed':
      return 'bg-red-100 text-red-700 border-red-200'
    case 'paused':
      return 'bg-yellow-100 text-yellow-700 border-yellow-200'
    default:
      return 'bg-gray-100 text-gray-700 border-gray-200'
  }
}

function getStatusLabel(status: PipelineStatus): string {
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

export function Header({ pipelineStatus, onRunPipeline, onStopPipeline }: HeaderProps) {
  const isRunning = pipelineStatus === 'running'

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold text-gray-900">
            Shopify UI Audit Tool
          </h1>
          <span
            className={cn(
              'px-2.5 py-0.5 text-xs font-medium rounded-full border',
              getStatusBadgeColor(pipelineStatus),
              isRunning && 'animate-pulse'
            )}
          >
            {getStatusLabel(pipelineStatus)}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {isRunning ? (
            <button
              onClick={onStopPipeline}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                'bg-red-600 text-white hover:bg-red-700',
                'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2'
              )}
            >
              Stop Pipeline
            </button>
          ) : (
            <button
              onClick={onRunPipeline}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                'bg-blue-600 text-white hover:bg-blue-700',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              )}
            >
              Run Pipeline
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
