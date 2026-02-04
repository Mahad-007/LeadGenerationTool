// Audit Types - Based on /audits/audit_results.json

export interface AuditMetadata {
  generated_at: string
  total_audited: number
  successful: number
  failed: number
  screenshots_dir: string
  analysis_completed_at?: string
  total_analyzed?: number
}

export interface Viewport {
  width: number
  height: number
}

export type ViewportType = 'desktop' | 'mobile'

export interface ConsoleErrorLocation {
  url?: string
  lineNumber?: number
  columnNumber?: number
}

export interface ConsoleError {
  type: 'error' | 'warning'
  text: string
  location?: ConsoleErrorLocation
}

export interface PerformanceMetrics {
  lcp: number | null
  fcp: number | null
  dom_content_loaded: number | null
  load_complete: number | null
  ttfb: number | null
}

export interface CtaInfo {
  text: string
  top: number
  visible: boolean
  tagName: string
}

export interface HeroInfo {
  height: number
  hasImage: boolean
}

export interface DomInfo {
  title: string
  h1: string
  ctas: CtaInfo[]
  ctasAboveFold: number
  ctasBelowFold: number
  heroInfo: HeroInfo
  brokenImages: string[]
  internalLinksCount: number
  viewportHeight: number
  pageHeight: number
  foldLine: number
}

export interface LinkIssue {
  type: string
  href: string
  text: string
}

export interface ViewportAudit {
  viewport_type: ViewportType
  viewport: Viewport
  screenshot_path: string
  console_errors: ConsoleError[]
  performance_metrics: PerformanceMetrics
  dom_info: DomInfo
  link_issues: LinkIssue[]
  error: string | null
}

export type IssueCategory =
  | 'typography'
  | 'layout'
  | 'images'
  | 'mobile'
  | 'contrast'
  | 'hierarchy'

export type IssueSeverity = 'high' | 'medium' | 'low'

export interface Issue {
  id: string
  category: IssueCategory
  severity: IssueSeverity
  title: string
  description: string
  location: string
  evidence: string
  recommendation: string
}

export interface AnalysisSummary {
  total_issues: number
  high_severity: number
  medium_severity: number
  low_severity: number
  primary_concern: string
}

export interface Analysis {
  url: string
  analyzed_at: string
  issues: Issue[]
  summary: AnalysisSummary
  error: string | null
  parse_error?: string
  raw_response?: string
}

export interface Audit {
  url: string
  audited_at: string
  desktop: ViewportAudit | null
  mobile: ViewportAudit | null
  error: string | null
  analysis?: Analysis
}

export interface AuditResponse {
  metadata: AuditMetadata
  audits: Audit[]
}
