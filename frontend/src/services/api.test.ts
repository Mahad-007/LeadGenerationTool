import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  pipelineApi,
  discoveryApi,
  verificationApi,
  auditApi,
  outreachApi,
  getWebSocketUrl,
} from './api'

const mockFetch = vi.fn()

beforeEach(() => {
  global.fetch = mockFetch
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('pipelineApi', () => {
  describe('getStatus', () => {
    it('returns pipeline state on success', async () => {
      const mockState = {
        status: 'idle',
        current_step: null,
        run_id: null,
        steps: {},
        started_at: null,
        completed_at: null,
        error: null,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockState),
      })

      const result = await pipelineApi.getStatus()

      expect(result.data).toEqual(mockState)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/pipeline/status',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('returns error on failed request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ detail: 'Server error' }),
      })

      const result = await pipelineApi.getStatus()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Server error')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await pipelineApi.getStatus()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error')
    })
  })

  describe('run', () => {
    it('starts pipeline and returns run response', async () => {
      const mockResponse = {
        success: true,
        message: 'Pipeline started',
        run_id: 'abc-123',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await pipelineApi.run({ niche: 'shoes' })

      expect(result.data).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/pipeline/run',
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  describe('stop', () => {
    it('stops pipeline and returns stop response', async () => {
      const mockResponse = {
        success: true,
        message: 'Pipeline stopped',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await pipelineApi.stop()

      expect(result.data).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/pipeline/stop',
        expect.objectContaining({ method: 'POST' })
      )
    })
  })
})

describe('discoveryApi', () => {
  it('fetches discovery data', async () => {
    const mockData = {
      metadata: {
        generated_at: '2024-01-01T00:00:00Z',
        total_niches: 5,
        total_urls: 100,
      },
      discoveries: [],
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const result = await discoveryApi.get()

    expect(result.data).toEqual(mockData)
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/discovery',
      expect.any(Object)
    )
  })

  it('runs discovery step', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, message: 'Started' }),
    })

    const result = await discoveryApi.run()

    expect(result.data?.success).toBe(true)
  })
})

describe('verificationApi', () => {
  it('fetches verification data', async () => {
    const mockData = {
      metadata: {
        generated_at: '2024-01-01T00:00:00Z',
        total_verified: 50,
        shopify_count: 30,
        non_shopify_count: 20,
      },
      shopify_sites: [],
      verification_log: [],
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const result = await verificationApi.get()

    expect(result.data).toEqual(mockData)
  })
})

describe('auditApi', () => {
  it('fetches audit data', async () => {
    const mockData = {
      metadata: {
        generated_at: '2024-01-01T00:00:00Z',
        total_sites: 10,
        successful: 8,
        failed: 2,
      },
      audits: [],
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const result = await auditApi.get()

    expect(result.data).toEqual(mockData)
  })

  it('generates correct screenshot URL', () => {
    const url = auditApi.getScreenshotUrl('test-screenshot.png')
    expect(url).toBe('http://localhost:8000/api/audit/screenshot/test-screenshot.png')
  })
})

describe('outreachApi', () => {
  it('fetches outreach data', async () => {
    const mockData = {
      metadata: {
        generated_at: '2024-01-01T00:00:00Z',
        total_drafts: 25,
        with_emails: 20,
        without_emails: 5,
      },
      drafts: [],
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const result = await outreachApi.get()

    expect(result.data).toEqual(mockData)
  })

  it('updates email draft', async () => {
    const mockDraft = {
      store_url: 'https://example.com',
      subject: 'Updated subject',
      body: 'Updated body',
      to_emails: [],
      issue_referenced: { title: 'Test', category: 'performance', severity: 'high' },
      social: { instagram: null, facebook: null, twitter: null, linkedin: null },
      status: 'draft',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDraft),
    })

    const result = await outreachApi.update('https://example.com', {
      subject: 'Updated subject',
    })

    expect(result.data?.subject).toBe('Updated subject')
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/outreach/https%3A%2F%2Fexample.com',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ subject: 'Updated subject' }),
      })
    )
  })
})

describe('getWebSocketUrl', () => {
  it('returns WebSocket URL', () => {
    const url = getWebSocketUrl()
    expect(url).toBe('ws://localhost:8000/ws/pipeline')
  })
})
