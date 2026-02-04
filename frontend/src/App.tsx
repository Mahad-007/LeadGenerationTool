import { useState, useCallback, useEffect, useMemo } from 'react'
import { AppShell } from './components/layout/AppShell'
import { Dashboard } from './components/dashboard/Dashboard'
import { PipelineConfigModal } from './components/pipeline/PipelineConfigModal'
import { ScreenshotViewer } from './components/audit/ScreenshotViewer'
import { EmailDraftEditor } from './components/outreach/EmailDraftEditor'
import { DataTable } from './components/shared/DataTable'
import { EmptyState } from './components/shared/EmptyState'
import { useWebSocket } from './hooks/useWebSocket'
import { usePipelineState } from './hooks/usePipelineState'
import { pipelineApi, discoveryApi, auditApi, outreachApi, getWebSocketUrl } from './services/api'
import type { DiscoveryResponse, AuditResponse, OutreachResponse } from './services/api'
import { ErrorAlert } from './components/shared/ErrorAlert'
import type { PipelineStep, PipelineConfig, StepStatus, EmailDraft, ViewportAudit } from './types'

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

type ViewType = PipelineStep | 'dashboard'

function App() {
  const [activeView, setActiveView] = useState<ViewType>('dashboard')
  const [discoveryData, setDiscoveryData] = useState<DiscoveryResponse | null>(null)
  const [auditData, setAuditData] = useState<AuditResponse | null>(null)
  const [outreachData, setOutreachData] = useState<OutreachResponse | null>(null)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
      return
    }
    setShowConfigModal(false)
  }, [])

  const handleStartAuditFromDashboard = useCallback(async (config: { niche: string; maxSites: number; senderName: string }) => {
    const result = await pipelineApi.run({
      niche: config.niche,
      maxSites: config.maxSites,
    })
    if (result.error) {
      console.error('Failed to start pipeline:', result.error)
    }
  }, [])

  const handleStopPipeline = useCallback(async () => {
    await pipelineApi.stop()
  }, [])

  const handleNavigate = useCallback((view: ViewType) => {
    setActiveView(view)
  }, [])

  // Fetch data when view changes
  const fetchViewData = useCallback(async () => {
    setError(null)
    try {
      if (activeView === 'discovery' || activeView === 'dashboard') {
        const result = await discoveryApi.get()
        if (result.error) throw new Error(result.error)
        if (result.data) setDiscoveryData(result.data)
      }
      if (activeView === 'audit' || activeView === 'dashboard') {
        const result = await auditApi.get()
        if (result.error) throw new Error(result.error)
        if (result.data) setAuditData(result.data)
      }
      if (activeView === 'outreach' || activeView === 'dashboard') {
        const result = await outreachApi.get()
        if (result.error) throw new Error(result.error)
        if (result.data) setOutreachData(result.data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
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

  // Calculate stats for dashboard
  const dashboardStats = useMemo(() => {
    const discovered = discoveryData?.discoveries?.reduce(
      (acc, d) => acc + (d.urls?.length || 0),
      0
    ) || 0

    const verified = auditData?.audits?.length || 0

    // Count issues from audits (issues are in the audit analysis, not directly on audit)
    const issues = 0 // TODO: Add proper issue counting when analysis data is available

    const emailsReady = outreachData?.drafts?.length || 0

    return { discovered, verified, issues, emailsReady }
  }, [discoveryData, auditData, outreachData])

  // Transform audit data into stores for dashboard
  const dashboardStores = useMemo(() => {
    if (!auditData?.audits) return []

    return auditData.audits.map((audit) => {
      const draft = outreachData?.drafts?.find((d) => d.store_url === audit.url)

      return {
        name: audit.url.replace(/^https?:\/\//, '').replace(/\/$/, '').split('.')[0],
        url: audit.url.replace(/^https?:\/\//, ''),
        confidence: 100,
        issues: [] as string[], // Simplified - issues come from analysis step
        contact: draft?.to_emails?.[0] || '',
      }
    })
  }, [auditData, outreachData])

  const renderContent = () => {
    if (error) {
      return (
        <div className="max-w-6xl mx-auto px-6 py-16">
          <ErrorAlert
            title="Error loading data"
            message={error}
            onDismiss={() => setError(null)}
          />
        </div>
      )
    }

    switch (activeView) {
      case 'dashboard':
        return (
          <Dashboard
            pipelineState={pipelineState}
            stepStatuses={stepStatuses}
            stats={dashboardStats}
            stores={dashboardStores}
            onStartAudit={handleStartAuditFromDashboard}
          />
        )

      case 'discovery':
        const discoveryRows: DiscoveryRow[] = discoveryData?.discoveries?.flatMap((d) =>
          d.urls.map((url: string) => ({ niche: d.niche, url, source: d.source }))
        ) || []

        return (
          <div className="max-w-6xl mx-auto px-6 py-16">
            <h1 className="text-3xl font-semibold tracking-tight mb-2">Discovered Sites</h1>
            <p className="text-gray-500 mb-12">
              Sites found during the discovery phase
            </p>
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
          <div className="max-w-6xl mx-auto px-6 py-16">
            <h1 className="text-3xl font-semibold tracking-tight mb-2">Audit Results</h1>
            <p className="text-gray-500 mb-12">
              Screenshots and analysis from audited stores
            </p>
            {(auditData?.audits?.length ?? 0) > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {auditData!.audits.map((audit) => (
                  <ScreenshotViewer
                    key={audit.url}
                    url={audit.url}
                    desktop={audit.desktop as ViewportAudit | null}
                    mobile={audit.mobile as ViewportAudit | null}
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
          <div className="max-w-6xl mx-auto px-6 py-16">
            <h1 className="text-3xl font-semibold tracking-tight mb-2">Email Drafts</h1>
            <p className="text-gray-500 mb-12">
              Generated outreach emails ready to send
            </p>
            {(outreachData?.drafts?.length ?? 0) > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {outreachData!.drafts.map((draft) => (
                  <EmailDraftEditor
                    key={draft.store_url}
                    draft={draft as EmailDraft}
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
          <Dashboard
            pipelineState={pipelineState}
            stepStatuses={stepStatuses}
            stats={dashboardStats}
            stores={dashboardStores}
            onStartAudit={handleStartAuditFromDashboard}
          />
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
        {renderContent()}
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
