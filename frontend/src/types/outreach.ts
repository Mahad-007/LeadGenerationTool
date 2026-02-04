// Outreach Types - Based on /outreach/drafts/drafts_summary.json

import type { SocialLinks } from './contacts'

export interface OutreachMetadata {
  generated_at: string
  total_drafts?: number
}

export interface DraftInfo {
  url: string
  file: string
  subject: string
  to_emails: string[]
  issue_category: string
}

export interface IssueReferenced {
  title: string
  category: string
  severity: string
}

export interface EmailDraft {
  store_url: string
  subject: string
  body: string
  to_emails: string[]
  social: SocialLinks
  issue_referenced: IssueReferenced
}

export interface DraftsSummary {
  generated_at: string
  drafts: DraftInfo[]
}

export interface OutreachResponse {
  metadata: OutreachMetadata
  drafts: DraftInfo[]
}
