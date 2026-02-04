import type { ReactNode } from 'react'
import type { PipelineStep, PipelineStatus, StepStatus } from '@/types'
import { Header } from './Header'

export interface AppShellProps {
  children: ReactNode
  pipelineStatus: PipelineStatus
  currentStep: PipelineStep | null
  stepStatuses: Record<PipelineStep, StepStatus>
  onRunPipeline: () => void
  onStopPipeline: () => void
  onNavigate: (step: PipelineStep | 'dashboard') => void
  activeView?: PipelineStep | 'dashboard'
}

export function AppShell({
  children,
  pipelineStatus,
  onRunPipeline,
  onStopPipeline,
  onNavigate,
  activeView,
}: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header
        pipelineStatus={pipelineStatus}
        onRunPipeline={onRunPipeline}
        onStopPipeline={onStopPipeline}
        onNavigate={onNavigate}
        activeView={activeView}
      />

      <main className="flex-1">
        {children}
      </main>

      {/* Minimal Footer */}
      <footer className="text-center py-12 border-t border-gray-200 mt-20">
        <p className="text-sm text-gray-400">
          ShopifyAudit — Lead generation for UI consultants
        </p>
      </footer>
    </div>
  )
}
