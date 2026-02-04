/**
 * API client for Shopify UI Audit backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        data: null,
        error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
      }
    }

    const data = await response.json()
    return { data, error: null }
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    }
  }
}

// Pipeline API
export interface PipelineRunConfig {
  niche: string
  maxSites?: number
}

export const pipelineApi = {
  getStatus: () => fetchApi<PipelineState>('/api/pipeline/status'),
  run: (config: PipelineRunConfig) =>
    fetchApi<PipelineRunResponse>('/api/pipeline/run', {
      method: 'POST',
      body: JSON.stringify({
        niche: config.niche,
        max_sites: config.maxSites ?? 10,
      }),
    }),
  stop: () => fetchApi<PipelineStopResponse>('/api/pipeline/stop', { method: 'POST' }),
}

// Discovery API
export const discoveryApi = {
  get: () => fetchApi<DiscoveryResponse>('/api/discovery'),
  run: () => fetchApi<StepRunResponse>('/api/discovery/run', { method: 'POST' }),
}

// Verification API
export const verificationApi = {
  get: () => fetchApi<VerificationResponse>('/api/verification'),
  run: () => fetchApi<StepRunResponse>('/api/verification/run', { method: 'POST' }),
}

// Audit API
export const auditApi = {
  get: () => fetchApi<AuditResponse>('/api/audit'),
  run: () => fetchApi<StepRunResponse>('/api/audit/run', { method: 'POST' }),
  getScreenshotUrl: (filename: string) => `${API_BASE_URL}/api/audit/screenshot/${filename}`,
}

// Outreach API
export const outreachApi = {
  get: () => fetchApi<OutreachResponse>('/api/outreach'),
  run: () => fetchApi<StepRunResponse>('/api/outreach/run', { method: 'POST' }),
  update: (url: string, data: EmailDraftUpdate) =>
    fetchApi<EmailDraft>(`/api/outreach/${encodeURIComponent(url)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
}

// Types (matching backend models)
export interface PipelineState {
  status: 'idle' | 'running' | 'completed' | 'failed'
  current_step: string | null
  run_id: string | null
  steps: Record<string, StepState>
  started_at: string | null
  completed_at: string | null
  error: string | null
}

export interface StepState {
  status: string
  progress: number
  message: string | null
  error: string | null
  items_processed: number
  items_total: number
  started_at: string | null
  completed_at: string | null
}

export interface PipelineRunResponse {
  success: boolean
  message: string
  run_id: string | null
}

export interface PipelineStopResponse {
  success: boolean
  message: string
}

export interface StepRunResponse {
  success: boolean
  message: string
}

export interface DiscoveryResponse {
  metadata: {
    generated_at: string
    total_niches: number
    total_urls: number
  }
  discoveries: Discovery[]
}

export interface Discovery {
  niche: string
  discovered_at: string
  total_urls: number
  urls: string[]
  source: 'database' | 'search_engines'
}

export interface VerificationResponse {
  metadata: {
    generated_at: string
    total_verified: number
    shopify_count: number
    non_shopify_count: number
  }
  shopify_sites: ShopifySite[]
  verification_log: ShopifySite[]
}

export interface ShopifySite {
  url: string
  is_shopify: boolean
  confidence: number
  signals_found: string[]
  verified_at: string
  error: string | null
}

export interface AuditResponse {
  metadata: {
    generated_at: string
    total_sites: number
    successful: number
    failed: number
  }
  audits: SiteAudit[]
}

export interface SiteAudit {
  url: string
  audited_at: string
  desktop: ViewportAudit | null
  mobile: ViewportAudit | null
  error: string | null
}

export interface ViewportAudit {
  viewport_type: 'desktop' | 'mobile'
  viewport: { width: number; height: number }
  screenshot_path: string
  console_errors: ConsoleError[]
  performance_metrics: PerformanceMetrics
  dom_info: DomInfo
  link_issues: LinkIssue[]
  error: string | null
}

export interface ConsoleError {
  type: string
  text: string
  location: {
    url: string | null
    lineNumber: number | null
    columnNumber: number | null
  } | null
}

export interface PerformanceMetrics {
  lcp: number | null
  fcp: number | null
  dom_content_loaded: number | null
  load_complete: number | null
  ttfb: number | null
}

export interface DomInfo {
  title: string | null
  h1: string | null
  ctas: CTA[]
  ctasAboveFold: number
  ctasBelowFold: number
  heroInfo: { height: number; hasImage: boolean } | null
  brokenImages: string[]
  internalLinksCount: number
  viewportHeight: number
  pageHeight: number
  foldLine: number
}

export interface CTA {
  text: string
  href: string | null
  position: 'above_fold' | 'below_fold'
}

export interface LinkIssue {
  url: string
  status_code: number | null
  issue_type: string
  text: string | null
}

export interface OutreachResponse {
  metadata: {
    generated_at: string
    total_drafts: number
    with_emails: number
    without_emails: number
  }
  drafts: EmailDraft[]
}

export interface EmailDraft {
  store_url: string
  to_emails: string[]
  subject: string
  body: string
  issue_referenced: {
    title: string
    category: string
    severity: 'high' | 'medium' | 'low'
  }
  social: {
    instagram: string | null
    facebook: string | null
    twitter: string | null
    linkedin: string | null
  }
  status: 'draft' | 'sent' | 'replied'
  created_at: string
  updated_at: string | null
}

export interface EmailDraftUpdate {
  subject?: string
  body?: string
  status?: 'draft' | 'sent' | 'replied'
}

// WebSocket URL helper
export function getWebSocketUrl(): string {
  const wsBase = API_BASE_URL.replace(/^http/, 'ws')
  return `${wsBase}/ws/pipeline`
}
