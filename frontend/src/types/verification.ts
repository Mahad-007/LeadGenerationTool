// Verification Types - Based on /verification/shopify_sites.json

export interface VerificationMetadata {
  generated_at: string
  total_verified: number
  shopify_count: number
  non_shopify_count: number
  min_confidence_threshold: number
}

export interface ShopifySite {
  url: string
  is_shopify: boolean
  confidence: number
  signals_found: string[]
  verified_at: string
  error: string | null
}

export interface VerificationResponse {
  metadata: VerificationMetadata
  shopify_sites: ShopifySite[]
  verification_log: ShopifySite[]
}
