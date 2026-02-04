import { cn } from '@/lib/utils'
import type { PipelineStep, StepStatus } from '@/types'
import { PIPELINE_STEPS, STEP_LABELS } from '@/types'

export interface SidebarProps {
  currentStep: PipelineStep | null
  stepStatuses: Record<PipelineStep, StepStatus>
  onNavigate: (step: PipelineStep) => void
  activeView?: PipelineStep
}

function getStatusIcon(status: StepStatus): string {
  switch (status) {
    case 'completed':
      return '✓'
    case 'running':
      return '●'
    case 'failed':
      return '✗'
    default:
      return ''
  }
}

function getStatusColor(status: StepStatus): string {
  switch (status) {
    case 'completed':
      return 'text-green-500 border-green-500 bg-green-50'
    case 'running':
      return 'text-blue-500 border-blue-500 bg-blue-50 animate-pulse'
    case 'failed':
      return 'text-red-500 border-red-500 bg-red-50'
    case 'pending':
      return 'text-gray-400 border-gray-300 bg-gray-50'
    default:
      return 'text-gray-500 border-gray-300 bg-white'
  }
}

export function Sidebar({ currentStep, stepStatuses, onNavigate, activeView }: SidebarProps) {
  return (
    <nav
      className="w-64 bg-gray-50 border-r border-gray-200 h-full flex flex-col"
      aria-label="Pipeline steps"
    >
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
          Pipeline Steps
        </h2>
      </div>

      <ul className="flex-1 py-2 space-y-1">
        {PIPELINE_STEPS.map((step, index) => {
          const status = stepStatuses[step]
          const isActive = currentStep === step || activeView === step
          const statusIcon = getStatusIcon(status)

          return (
            <li key={step}>
              <button
                type="button"
                onClick={() => onNavigate(step)}
                data-status={status}
                aria-current={isActive ? 'page' : undefined}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors text-left',
                  'hover:bg-gray-100',
                  isActive && 'bg-blue-50 border-r-2 border-blue-500',
                  status === 'failed' && 'bg-red-50'
                )}
              >
                <span
                  className={cn(
                    'flex items-center justify-center w-6 h-6 rounded-full border text-xs font-medium',
                    getStatusColor(status)
                  )}
                >
                  {statusIcon || index + 1}
                </span>
                <span
                  className={cn(
                    'font-medium',
                    isActive ? 'text-blue-700' : 'text-gray-700',
                    status === 'completed' && 'text-green-700',
                    status === 'failed' && 'text-red-700'
                  )}
                >
                  {STEP_LABELS[step]}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
