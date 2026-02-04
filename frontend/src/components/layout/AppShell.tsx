import type { ReactNode } from 'react'
import type { PipelineStep, PipelineStatus, StepStatus } from '@/types'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export interface AppShellProps {
  children: ReactNode
  pipelineStatus: PipelineStatus
  currentStep: PipelineStep | null
  stepStatuses: Record<PipelineStep, StepStatus>
  onRunPipeline: () => void
  onStopPipeline: () => void
  onNavigate: (step: PipelineStep) => void
  activeView?: PipelineStep
}

export function AppShell({
  children,
  pipelineStatus,
  currentStep,
  stepStatuses,
  onRunPipeline,
  onStopPipeline,
  onNavigate,
  activeView,
}: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <Header
        pipelineStatus={pipelineStatus}
        onRunPipeline={onRunPipeline}
        onStopPipeline={onStopPipeline}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          currentStep={currentStep}
          stepStatuses={stepStatuses}
          onNavigate={onNavigate}
          activeView={activeView}
        />

        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
