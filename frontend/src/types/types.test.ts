import { describe, it, expect } from 'vitest'
import type {
  DiscoveryResponse,
  VerificationResponse,
  AuditResponse,
  ContactsResponse,
  DraftsSummary,
  PipelineState,
  StepState,
  WebSocketEvent,
} from './index'
import {
  createInitialPipelineState,
  createInitialStepState,
  PIPELINE_STEPS,
  STEP_LABELS,
} from './index'

// Sample data matching actual JSON outputs
const discoveryData: DiscoveryResponse = {
  metadata: {
    generated_at: '2026-01-26T11:28:09.868654+00:00',
    total_niches: 1,
    total_urls: 5,
  },
  discoveries: [
    {
      niche: 'pet supplies',
      discovered_at: '2026-01-26T11:28:09.868605+00:00',
      total_urls: 5,
      urls: ['https://allbirds.com', 'https://colourpop.com'],
      search_metadata: [
        {
          engine: 'built_in_database',
          query: 'pet supplies',
          results_count: 5,
        },
      ],
      source: 'database',
    },
  ],
}

const verificationData: VerificationResponse = {
  metadata: {
    generated_at: '2026-01-26T11:29:04.744489+00:00',
    total_verified: 5,
    shopify_count: 5,
    non_shopify_count: 0,
    min_confidence_threshold: 70,
  },
  shopify_sites: [
    {
      url: 'https://colourpop.com',
      is_shopify: true,
      confidence: 100,
      signals_found: ['cdn.shopify.com', 'myshopify.com'],
      verified_at: '2026-01-26T11:28:15.364921+00:00',
      error: null,
    },
  ],
  verification_log: [],
}

const contactsData: ContactsResponse = {
  metadata: {
    generated_at: '2026-01-26T11:30:27.456094+00:00',
    total_sites: 1,
    sites_with_contacts: 1,
    total_emails_found: 0,
    total_social_found: 3,
  },
  contacts: [
    {
      url: 'https://fashionnova.com',
      extracted_at: '2026-01-26T11:30:03.300944+00:00',
      emails: [],
      phones: ['(818) 347-6500'],
      social: {
        instagram: 'https://www.instagram.com/fashionnova',
        tiktok: 'https://www.tiktok.com/@fashionnova',
        facebook: 'https://www.facebook.com/FashionNova',
      },
      contact_page_found: true,
      sources: ['homepage', '/pages/contact'],
      error: null,
    },
  ],
}

const draftsSummaryData: DraftsSummary = {
  generated_at: '2026-01-26T11:30:31.904595+00:00',
  drafts: [],
}

const auditData: AuditResponse = {
  metadata: {
    generated_at: '2026-01-26T11:29:31.118983+00:00',
    total_audited: 1,
    successful: 1,
    failed: 0,
    screenshots_dir: '/path/to/screenshots',
  },
  audits: [
    {
      url: 'https://gymshark.com',
      audited_at: '2026-01-26T11:29:14.095975+00:00',
      desktop: {
        viewport_type: 'desktop',
        viewport: { width: 1440, height: 900 },
        screenshot_path: '/path/to/screenshot.png',
        console_errors: [{ type: 'error', text: 'CORS error' }],
        performance_metrics: {
          lcp: 3624,
          fcp: 1936,
          dom_content_loaded: 2389,
          load_complete: 7785,
          ttfb: 1476,
        },
        dom_info: {
          title: 'Gymshark',
          h1: 'Hero Title',
          ctas: [],
          ctasAboveFold: 10,
          ctasBelowFold: 5,
          heroInfo: { height: 125, hasImage: true },
          brokenImages: [],
          internalLinksCount: 100,
          viewportHeight: 900,
          pageHeight: 5000,
          foldLine: 900,
        },
        link_issues: [] as { type: string; href: string; text: string }[],
        error: null,
      },
      mobile: null,
      error: null,
    },
  ],
}

describe('Type Definitions', () => {
  describe('DiscoveryResponse', () => {
    it('should match the expected structure', () => {
      expect(discoveryData.metadata.total_niches).toBe(1)
      expect(discoveryData.discoveries[0].niche).toBe('pet supplies')
      expect(discoveryData.discoveries[0].source).toBe('database')
      expect(discoveryData.discoveries[0].search_metadata[0].engine).toBe(
        'built_in_database'
      )
    })

    it('should have valid search engine types', () => {
      const validEngines = ['google', 'bing', 'duckduckgo', 'built_in_database']
      discoveryData.discoveries.forEach((discovery) => {
        discovery.search_metadata.forEach((meta) => {
          expect(validEngines).toContain(meta.engine)
        })
      })
    })
  })

  describe('VerificationResponse', () => {
    it('should match the expected structure', () => {
      expect(verificationData.metadata.total_verified).toBe(5)
      expect(verificationData.shopify_sites[0].is_shopify).toBe(true)
      expect(verificationData.shopify_sites[0].confidence).toBe(100)
    })

    it('should have valid confidence values', () => {
      verificationData.shopify_sites.forEach((site) => {
        expect(site.confidence).toBeGreaterThanOrEqual(0)
        expect(site.confidence).toBeLessThanOrEqual(100)
      })
    })
  })

  describe('ContactsResponse', () => {
    it('should match the expected structure', () => {
      expect(contactsData.metadata.total_sites).toBe(1)
      expect(contactsData.contacts[0].contact_page_found).toBe(true)
    })

    it('should have valid social links', () => {
      const contact = contactsData.contacts[0]
      expect(contact.social.instagram).toContain('instagram.com')
      expect(contact.social.facebook).toContain('facebook.com')
    })
  })

  describe('DraftsSummary', () => {
    it('should match the expected structure', () => {
      expect(draftsSummaryData.generated_at).toBeDefined()
      expect(Array.isArray(draftsSummaryData.drafts)).toBe(true)
    })
  })

  describe('AuditResponse', () => {
    it('should match the expected structure', () => {
      expect(auditData.metadata.total_audited).toBe(1)
      expect(auditData.metadata.successful).toBe(1)
      expect(auditData.audits[0].url).toBe('https://gymshark.com')
    })

    it('should have valid viewport audit data', () => {
      const desktop = auditData.audits[0].desktop
      expect(desktop?.viewport_type).toBe('desktop')
      expect(desktop?.viewport.width).toBe(1440)
      expect(desktop?.performance_metrics.lcp).toBe(3624)
    })

    it('should support nullable mobile viewport', () => {
      expect(auditData.audits[0].mobile).toBeNull()
    })
  })
})

describe('Pipeline Types', () => {
  describe('createInitialStepState', () => {
    it('should create a valid initial step state', () => {
      const state: StepState = createInitialStepState()
      expect(state.status).toBe('idle')
      expect(state.progress).toBe(0)
      expect(state.message).toBe('')
    })
  })

  describe('createInitialPipelineState', () => {
    it('should create a valid initial pipeline state', () => {
      const state: PipelineState = createInitialPipelineState()
      expect(state.status).toBe('idle')
      expect(state.currentStep).toBeNull()
      expect(Object.keys(state.steps)).toHaveLength(6)
    })

    it('should have all pipeline steps initialized', () => {
      const state = createInitialPipelineState()
      PIPELINE_STEPS.forEach((step) => {
        expect(state.steps[step]).toBeDefined()
        expect(state.steps[step].status).toBe('idle')
      })
    })
  })

  describe('PIPELINE_STEPS', () => {
    it('should have all 6 steps in correct order', () => {
      expect(PIPELINE_STEPS).toEqual([
        'discovery',
        'verification',
        'audit',
        'analysis',
        'contacts',
        'outreach',
      ])
    })
  })

  describe('STEP_LABELS', () => {
    it('should have labels for all steps', () => {
      PIPELINE_STEPS.forEach((step) => {
        expect(STEP_LABELS[step]).toBeDefined()
        expect(typeof STEP_LABELS[step]).toBe('string')
      })
    })
  })
})

describe('WebSocket Event Types', () => {
  it('should support connected event', () => {
    const event: WebSocketEvent = {
      type: 'connected',
      clientId: 'test-123',
    }
    expect(event.type).toBe('connected')
  })

  it('should support step_progress event', () => {
    const event: WebSocketEvent = {
      type: 'step_progress',
      step: 'discovery',
      current: 5,
      total: 10,
      percentage: 50,
      message: 'Processing...',
    }
    expect(event.type).toBe('step_progress')
    expect(event.percentage).toBe(50)
  })

  it('should support pipeline_completed event', () => {
    const event: WebSocketEvent = {
      type: 'pipeline_completed',
      summary: {
        totalDuration: 120000,
        stepsCompleted: 6,
        totalSteps: 6,
        sitesProcessed: 5,
      },
    }
    expect(event.type).toBe('pipeline_completed')
  })
})
