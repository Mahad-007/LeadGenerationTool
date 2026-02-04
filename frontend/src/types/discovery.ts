// Discovery Types - Based on /discovery/discovered_sites.json

export interface DiscoveryMetadata {
  generated_at: string
  total_niches: number
  total_urls: number
}

export type SearchEngine = 'google' | 'bing' | 'duckduckgo' | 'built_in_database'
export type DiscoverySource = 'database' | 'search_engines'

export interface SearchMetadata {
  engine: SearchEngine
  query: string
  results_count: number
}

export interface Discovery {
  niche: string
  discovered_at: string
  total_urls: number
  urls: string[]
  search_metadata: SearchMetadata[]
  source: DiscoverySource
}

export interface DiscoveryResponse {
  metadata: DiscoveryMetadata
  discoveries: Discovery[]
}
