import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { PipelineState, PipelineStep, StepStatus } from '@/types'
import { PIPELINE_STEPS, STEP_LABELS } from '@/types'

interface DashboardProps {
  pipelineState: PipelineState
  stepStatuses: Record<PipelineStep, StepStatus>
  stats: {
    discovered: number
    verified: number
    issues: number
    emailsReady: number
  }
  stores: Array<{
    name: string
    url: string
    confidence: number
    issues: string[]
    contact: string
  }>
  onStartAudit: (config: { niche: string; maxSites: number; senderName: string }) => void
}

const STEP_META: Record<PipelineStep, Record<StepStatus, string>> = {
  discovery: { idle: 'Waiting', pending: 'Waiting', running: 'Finding...', completed: '', failed: 'Failed' },
  verification: { idle: 'Waiting', pending: 'Waiting', running: 'Verifying...', completed: '', failed: 'Failed' },
  audit: { idle: 'Waiting', pending: 'Waiting', running: 'Auditing...', completed: '', failed: 'Failed' },
  analysis: { idle: 'Waiting', pending: 'Waiting', running: 'Analyzing...', completed: '', failed: 'Failed' },
  contacts: { idle: 'Waiting', pending: 'Waiting', running: 'Extracting...', completed: '', failed: 'Failed' },
  outreach: { idle: 'Waiting', pending: 'Waiting', running: 'Generating...', completed: '', failed: 'Failed' },
}

export function Dashboard({
  pipelineState,
  stepStatuses,
  stats,
  stores,
  onStartAudit,
}: DashboardProps) {
  const [filter, setFilter] = useState<'all' | 'issues' | 'ready'>('all')
  const [niche, setNiche] = useState('shoes')
  const [maxSites, setMaxSites] = useState(10)
  const [senderName, setSenderName] = useState('')

  const isRunning = pipelineState.status === 'running'

  const getStepMeta = (step: PipelineStep): string => {
    const status = stepStatuses[step]
    const stepState = pipelineState.steps[step]

    if (status === 'completed' && stepState.itemsProcessed) {
      return `${stepState.itemsProcessed} ${step === 'discovery' ? 'found' : step === 'verification' ? 'verified' : 'done'}`
    }
    if (status === 'running' && stepState.progress > 0) {
      return `${stepState.itemsProcessed || 0} of ${stats.verified || '?'}`
    }
    return STEP_META[step][status] || 'Waiting'
  }

  const filteredStores = stores.filter((store) => {
    if (filter === 'issues') return store.issues.length > 0
    if (filter === 'ready') return store.contact && store.issues.length > 0
    return true
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStartAudit({ niche, maxSites, senderName })
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      {/* Page Header */}
      <header className="mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 rounded-full text-sm text-gray-600 mb-4">
          <span className={cn(
            'w-1.5 h-1.5 rounded-full',
            isRunning ? 'bg-black animate-pulse' : 'bg-gray-400'
          )} />
          {isRunning ? 'Pipeline running' : 'Pipeline idle'}
        </div>
        <h1 className="text-3xl font-semibold tracking-tight mb-2">Dashboard</h1>
        <p className="text-gray-500">
          Discover and audit Shopify stores with UI opportunities
        </p>
      </header>

      {/* Pipeline Steps */}
      <section className="mb-20">
        <div className="text-xs font-medium uppercase tracking-widest text-gray-400 mb-6">
          Pipeline Progress
        </div>
        <div className="flex border border-gray-200 rounded-lg overflow-hidden">
          {PIPELINE_STEPS.map((step, index) => {
            const status = stepStatuses[step]
            const isActive = pipelineState.currentStep === step

            return (
              <div
                key={step}
                className={cn(
                  'flex-1 py-8 text-center border-r border-gray-200 last:border-r-0',
                  isActive && 'bg-gray-50'
                )}
              >
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-4 text-sm font-semibold',
                    status === 'completed' && 'bg-black text-white',
                    isActive && 'bg-white border-2 border-black text-black',
                    (status === 'pending' || status === 'idle') && 'bg-gray-100 text-gray-400'
                  )}
                >
                  {status === 'completed' ? '✓' : index + 1}
                </div>
                <div className="text-sm font-medium mb-1">{STEP_LABELS[step].split(' ')[0]}</div>
                <div className="text-sm text-gray-500">{getStepMeta(step)}</div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-4 gap-12 py-12 mb-20 border-t border-b border-gray-200">
        <div className="text-center">
          <div className="text-5xl font-semibold tracking-tight mb-2" style={{ letterSpacing: '-0.03em' }}>
            {stats.discovered}
          </div>
          <div className="text-sm text-gray-500">Stores discovered</div>
        </div>
        <div className="text-center">
          <div className="text-5xl font-semibold tracking-tight mb-2" style={{ letterSpacing: '-0.03em' }}>
            {stats.verified}
          </div>
          <div className="text-sm text-gray-500">Verified Shopify</div>
        </div>
        <div className="text-center">
          <div className="text-5xl font-semibold tracking-tight mb-2" style={{ letterSpacing: '-0.03em' }}>
            {stats.issues}
          </div>
          <div className="text-sm text-gray-500">UI issues found</div>
        </div>
        <div className="text-center">
          <div className="text-5xl font-semibold tracking-tight mb-2" style={{ letterSpacing: '-0.03em' }}>
            {stats.emailsReady}
          </div>
          <div className="text-sm text-gray-500">Emails ready</div>
        </div>
      </section>

      {/* Results Table */}
      <section className="mb-20">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-lg font-semibold">Audit Results</h2>
          <div className="filter-tabs-minimal">
            <button
              type="button"
              onClick={() => setFilter('all')}
              className={cn('filter-tab-minimal', filter === 'all' && 'active')}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setFilter('issues')}
              className={cn('filter-tab-minimal', filter === 'issues' && 'active')}
            >
              With Issues
            </button>
            <button
              type="button"
              onClick={() => setFilter('ready')}
              className={cn('filter-tab-minimal', filter === 'ready' && 'active')}
            >
              Ready
            </button>
          </div>
        </div>

        {filteredStores.length > 0 ? (
          <table className="table-minimal">
            <thead>
              <tr>
                <th>Store</th>
                <th>Confidence</th>
                <th>Issues</th>
                <th>Contact</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filteredStores.map((store) => (
                <tr key={store.url}>
                  <td>
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center font-semibold text-sm">
                        {store.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-medium">{store.name}</div>
                        <div className="text-sm text-gray-500">{store.url}</div>
                      </div>
                    </div>
                  </td>
                  <td className="text-sm font-medium">{store.confidence}%</td>
                  <td>
                    <div className="flex gap-1.5 flex-wrap">
                      {store.issues.map((issue) => (
                        <span key={issue} className="issue-tag-minimal">
                          {issue}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="text-sm text-gray-600">{store.contact}</td>
                  <td>
                    <a href="#" className="text-sm text-black font-medium hover:underline">
                      View →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-16 text-gray-500">
            <p>No stores to display. Run the pipeline to discover Shopify stores.</p>
          </div>
        )}
      </section>

      {/* New Audit Form */}
      <section className="bg-gray-50 rounded-xl p-12">
        <h3 className="text-lg font-semibold mb-8">Start New Audit</h3>
        <form onSubmit={handleSubmit} className="grid grid-cols-4 gap-6 items-end">
          <div>
            <label htmlFor="niche-select" className="form-label-minimal">Niche</label>
            <select
              id="niche-select"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              className="form-input-minimal"
            >
              <option value="shoes">Shoes & Footwear</option>
              <option value="fashion">Fashion & Apparel</option>
              <option value="jewelry">Jewelry</option>
              <option value="beauty">Beauty</option>
            </select>
          </div>
          <div>
            <label htmlFor="max-sites-input" className="form-label-minimal">Max Sites</label>
            <input
              id="max-sites-input"
              type="number"
              value={maxSites}
              onChange={(e) => setMaxSites(Number(e.target.value))}
              min={1}
              max={50}
              className="form-input-minimal"
            />
          </div>
          <div>
            <label htmlFor="sender-name-input" className="form-label-minimal">Your Name</label>
            <input
              id="sender-name-input"
              type="text"
              value={senderName}
              onChange={(e) => setSenderName(e.target.value)}
              placeholder="For email signatures"
              className="form-input-minimal"
            />
          </div>
          <button
            type="submit"
            disabled={isRunning}
            className={cn(
              'btn-minimal btn-minimal-primary h-[46px]',
              isRunning && 'opacity-50 cursor-not-allowed'
            )}
          >
            Start
          </button>
        </form>
      </section>
    </div>
  )
}
