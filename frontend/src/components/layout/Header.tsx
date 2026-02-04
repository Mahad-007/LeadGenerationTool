import { cn } from '@/lib/utils'
import type { PipelineStatus, PipelineStep } from '@/types'

export interface HeaderProps {
  pipelineStatus: PipelineStatus
  onRunPipeline: () => void
  onStopPipeline: () => void
  onNavigate?: (view: PipelineStep | 'dashboard') => void
  activeView?: PipelineStep | 'dashboard'
}

const NAV_ITEMS: { key: PipelineStep | 'dashboard'; label: string }[] = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'discovery', label: 'Discovery' },
  { key: 'audit', label: 'Audits' },
  { key: 'outreach', label: 'Outreach' },
]

export function Header({
  pipelineStatus,
  onRunPipeline,
  onStopPipeline,
  onNavigate,
  activeView = 'dashboard'
}: HeaderProps) {
  const isRunning = pipelineStatus === 'running'

  return (
    <header className="flex items-center justify-between px-12 py-6 border-b border-gray-200">
      {/* Logo */}
      <div className="font-bold text-lg tracking-tight">
        ShopifyAudit
      </div>

      {/* Navigation Links */}
      <nav className="flex items-center gap-8">
        {NAV_ITEMS.map((item) => (
          <button
            type="button"
            key={item.key}
            onClick={() => onNavigate?.(item.key)}
            className={cn(
              'nav-link-minimal',
              activeView === item.key && 'active'
            )}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <button type="button" className="btn-minimal btn-minimal-ghost">
          Help
        </button>
        {isRunning ? (
          <button
            type="button"
            onClick={onStopPipeline}
            className="btn-minimal bg-red-600 text-white hover:bg-red-700"
          >
            Stop Pipeline
          </button>
        ) : (
          <button
            type="button"
            onClick={onRunPipeline}
            className="btn-minimal btn-minimal-primary"
          >
            New Audit
          </button>
        )}
      </div>
    </header>
  )
}
