import { useState, useCallback, useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { PipelineStatus } from './components/pipeline/PipelineStatus'
import { StepCard } from './components/pipeline/StepCard'
import { PipelineConfigModal } from './components/pipeline/PipelineConfigModal'
import { ScreenshotViewer } from './components/audit/ScreenshotViewer'
import { EmailDraftEditor } from './components/outreach/EmailDraftEditor'
import { DataTable } from './components/shared/DataTable'
import { EmptyState } from './components/shared/EmptyState'
import { useWebSocket } from './hooks/useWebSocket'
import { usePipelineState } from './hooks/usePipelineState'
import { pipelineApi, discoveryApi, auditApi, outreachApi, getWebSocketUrl } from './services/api'
import type { PipelineStep, PipelineConfig, StepStatus, StepState, EmailDraft } from './types'

import { STEP_LABELS } from './types'

const STEP_ORDER: PipelineStep[] = [
  'discovery',
  'verification',
  'audit',
  'analysis',
  'contacts',
  'outreach',
]

interface DiscoveryRow {
  niche: string
  url: string
  source: string
}

function App() {
  const [activeView, setActiveView] = useState<PipelineStep>('discovery')
  const [discoveryData, setDiscoveryData] = useState<any>(null)
  const [auditData, setAuditData] = useState<any>(null)
  const [outreachData, setOutreachData] = useState<any>(null)
  const [showConfigModal, setShowConfigModal] = useState(false)

  // Pipeline state from WebSocket
  const { state: pipelineState, handleEvent } = usePipelineState()

  // WebSocket connection
  useWebSocket({
    url: getWebSocketUrl(),
    enabled: true,
    onMessage: (event) => {
      handleEvent(event)
    },
  })

  // Derive step statuses from pipeline state
  const stepStatuses: Record<PipelineStep, StepStatus> = STEP_ORDER.reduce(
    (acc, step) => {
      const stepState = pipelineState.steps[step]
      let status: StepStatus = 'pending'
      if (stepState?.status === 'running') status = 'running'
      else if (stepState?.status === 'completed') status = 'completed'
      else if (stepState?.status === 'failed') status = 'failed'
      acc[step] = status
      return acc
    },
    {} as Record<PipelineStep, StepStatus>
  )

  const handleRunPipeline = useCallback(() => {
    setShowConfigModal(true)
  }, [])

  const handleStartPipeline = useCallback(async (config: PipelineConfig) => {
    const result = await pipelineApi.run({
      niche: config.niche,
      maxSites: config.maxSites,
    })
    if (result.error) {
      console.error('Failed to start pipeline:', result.error)
      // Keep modal open on error so user can retry
      return
    }
    setShowConfigModal(false)
  }, [])

  const handleStopPipeline = useCallback(async () => {
    await pipelineApi.stop()
  }, [])

  const handleNavigate = useCallback((step: PipelineStep) => {
    setActiveView(step)
  }, [])

  // Fetch data when view changes
  const fetchViewData = useCallback(async () => {
    if (activeView === 'discovery') {
      const result = await discoveryApi.get()
      if (result.data) setDiscoveryData(result.data)
    } else if (activeView === 'audit') {
      const result = await auditApi.get()
      if (result.data) setAuditData(result.data)
    } else if (activeView === 'outreach') {
      const result = await outreachApi.get()
      if (result.data) setOutreachData(result.data)
    }
  }, [activeView])

  // Fetch on mount and view change
  useEffect(() => {
    fetchViewData()
  }, [fetchViewData])

  const handleSaveEmailDraft = useCallback(async (draft: EmailDraft) => {
    await outreachApi.update(draft.store_url, {
      subject: draft.subject,
      body: draft.body,
    })
    fetchViewData()
  }, [fetchViewData])

  const handleCopyEmailDraft = useCallback((draft: EmailDraft) => {
    const text = `Subject: ${draft.subject}\n\n${draft.body}`
    navigator.clipboard.writeText(text)
  }, [])

  // Calculate overall progress
  const completedSteps = STEP_ORDER.filter(
    (step) => stepStatuses[step] === 'completed'
  ).length
  const overallProgress = Math.round((completedSteps / STEP_ORDER.length) * 100)

  const renderContent = () => {
    switch (activeView) {
      case 'discovery':
        const discoveryRows: DiscoveryRow[] = discoveryData?.discoveries?.flatMap((d: any) =>
          d.urls.map((url: string) => ({ niche: d.niche, url, source: d.source }))
        ) || []

        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Discovered Sites</h2>
            {discoveryRows.length > 0 ? (
              <DataTable<DiscoveryRow>
                data={discoveryRows}
                columns={[
                  { key: 'niche', header: 'Niche', sortable: true },
                  { key: 'url', header: 'URL', sortable: true },
                  { key: 'source', header: 'Source', sortable: true },
                ]}
                rowKey="url"
              />
            ) : (
              <EmptyState
                title="No sites discovered"
                message="Run the pipeline to discover Shopify stores"
              />
            )}
          </div>
        )

      case 'audit':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Audit Results</h2>
            {auditData?.audits?.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {auditData.audits.map((audit: any) => (
                  <ScreenshotViewer
                    key={audit.url}
                    url={audit.url}
                    desktop={audit.desktop}
                    mobile={audit.mobile}
                    baseUrl="http://localhost:8000"
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No audits yet"
                message="Run the pipeline to audit discovered sites"
              />
            )}
          </div>
        )

      case 'outreach':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Email Drafts</h2>
            {outreachData?.drafts?.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {outreachData.drafts.map((draft: EmailDraft) => (
                  <EmailDraftEditor
                    key={draft.store_url}
                    draft={draft}
                    onSave={handleSaveEmailDraft}
                    onCopy={handleCopyEmailDraft}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No email drafts"
                message="Run the pipeline to generate outreach emails"
              />
            )}
          </div>
        )

      default:
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Pipeline Overview</h2>
            <PipelineStatus
              state={pipelineState}
              overallProgress={overallProgress}
              completedSteps={completedSteps}
              totalSteps={STEP_ORDER.length}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {STEP_ORDER.map((step, index) => {
                const stepState = pipelineState.steps[step]
                const cardState: StepState = {
                  status: (stepState?.status || 'pending') as StepStatus,
                  progress: stepState?.progress || 0,
                  message: stepState?.message || '',
                  error: stepState?.error,
                  itemsProcessed: stepState?.itemsProcessed,
                }
                return (
                  <StepCard
                    key={step}
                    step={step}
                    label={STEP_LABELS[step]}
                    stepNumber={index + 1}
                    state={cardState}
                    isActive={pipelineState.currentStep === step}
                  />
                )
              })}
            </div>
          </div>
        )
    }
  }

  return (
    <>
      <AppShell
        pipelineStatus={pipelineState.status}
        currentStep={pipelineState.currentStep}
        stepStatuses={stepStatuses}
        onRunPipeline={handleRunPipeline}
        onStopPipeline={handleStopPipeline}
        onNavigate={handleNavigate}
        activeView={activeView}
      >
        <div className="p-6">
          {renderContent()}
        </div>
      </AppShell>

      <PipelineConfigModal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onStart={handleStartPipeline}
      />
    </>
  )
}

export default App
