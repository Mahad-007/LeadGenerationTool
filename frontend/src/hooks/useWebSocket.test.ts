import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from './useWebSocket'
import type { WebSocketEvent } from '@/types'

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = []
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: ((error: Event) => void) | null = null
  readyState: number = 0 // WebSocket.CONNECTING
  url: string

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  // Call this manually in tests to simulate connection
  connect() {
    this.readyState = 1 // WebSocket.OPEN
    this.onopen?.()
  }

  close() {
    this.readyState = 3 // WebSocket.CLOSED
    this.onclose?.()
  }

  send = vi.fn()

  simulateMessage(data: WebSocketEvent) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }

  simulateMalformedMessage(data: string) {
    this.onmessage?.({ data })
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }

  static clear() {
    MockWebSocket.instances = []
  }

  static get CONNECTING() { return 0 }
  static get OPEN() { return 1 }
  static get CLOSING() { return 2 }
  static get CLOSED() { return 3 }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.clear()
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('connection', () => {
    it('connects to WebSocket server', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      expect(MockWebSocket.instances).toHaveLength(1)
      expect(MockWebSocket.instances[0].url).toBe('ws://localhost:8000/ws')
      expect(result.current.isConnected).toBe(false)

      // Simulate connection
      act(() => {
        MockWebSocket.instances[0].connect()
      })

      expect(result.current.isConnected).toBe(true)
    })

    it('handles connection errors', () => {
      const onError = vi.fn()
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws', onError })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      expect(result.current.isConnected).toBe(true)

      act(() => {
        MockWebSocket.instances[0].simulateError()
      })

      expect(onError).toHaveBeenCalled()
    })

    it('disconnects when component unmounts', () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      expect(result.current.isConnected).toBe(true)

      unmount()

      expect(MockWebSocket.instances[0].readyState).toBe(WebSocket.CLOSED)
    })

    it('calls onOpen callback when connection opens', () => {
      const onOpen = vi.fn()
      renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws', onOpen })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      expect(onOpen).toHaveBeenCalled()
    })

    it('calls onClose callback when connection closes', () => {
      const onClose = vi.fn()
      renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws', onClose })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
        MockWebSocket.instances[0].close()
      })

      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('messages', () => {
    it('receives and parses WebSocket messages', () => {
      const onMessage = vi.fn()
      renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws', onMessage })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      const testEvent: WebSocketEvent = {
        type: 'step_progress',
        step: 'discovery',
        current: 5,
        total: 10,
        percentage: 50,
        message: 'Processing...',
      }

      act(() => {
        MockWebSocket.instances[0].simulateMessage(testEvent)
      })

      expect(onMessage).toHaveBeenCalledWith(testEvent)
    })

    it('tracks last message received', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      const testEvent: WebSocketEvent = {
        type: 'connected',
        clientId: 'test-123',
      }

      act(() => {
        MockWebSocket.instances[0].simulateMessage(testEvent)
      })

      expect(result.current.lastMessage).toEqual(testEvent)
    })

    it('handles malformed JSON messages gracefully', () => {
      const onMessage = vi.fn()
      renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws', onMessage })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      act(() => {
        MockWebSocket.instances[0].simulateMalformedMessage('not valid json {{{')
      })

      expect(onMessage).not.toHaveBeenCalled()
      expect(console.warn).toHaveBeenCalledWith(
        'Failed to parse WebSocket message:',
        'not valid json {{{'
      )
    })
  })

  describe('send', () => {
    it('sends messages to WebSocket server', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      act(() => {
        result.current.send({ type: 'ping' })
      })

      expect(MockWebSocket.instances[0].send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'ping' })
      )
    })

    it('does not send when disconnected', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      // Don't connect - WebSocket is in CONNECTING state
      act(() => {
        result.current.send({ type: 'ping' })
      })

      expect(MockWebSocket.instances[0].send).not.toHaveBeenCalled()
    })
  })

  describe('reconnection', () => {
    it('does not connect when enabled is false', () => {
      renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws', enabled: false })
      )

      expect(MockWebSocket.instances).toHaveLength(0)
    })

    it('manual disconnect prevents reconnection', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      expect(result.current.isConnected).toBe(true)

      act(() => {
        result.current.disconnect()
      })

      expect(result.current.isConnected).toBe(false)
      // Should only have the original instance, no reconnection attempts
      expect(MockWebSocket.instances).toHaveLength(1)
    })

    it('manual reconnect creates new connection', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://localhost:8000/ws' })
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      expect(result.current.isConnected).toBe(true)
      expect(MockWebSocket.instances).toHaveLength(1)

      act(() => {
        result.current.reconnect()
      })

      // Should have created a new WebSocket instance
      expect(MockWebSocket.instances).toHaveLength(2)

      act(() => {
        MockWebSocket.instances[1].connect()
      })

      expect(result.current.isConnected).toBe(true)
    })
  })

  describe('callback stability', () => {
    it('uses latest callback refs to avoid stale closures', () => {
      let messageCount = 0
      const onMessage1 = vi.fn(() => { messageCount = 1 })
      const onMessage2 = vi.fn(() => { messageCount = 2 })

      const { rerender } = renderHook(
        ({ onMessage }) => useWebSocket({ url: 'ws://localhost:8000/ws', onMessage }),
        { initialProps: { onMessage: onMessage1 } }
      )

      act(() => {
        MockWebSocket.instances[0].connect()
      })

      // Update callback
      rerender({ onMessage: onMessage2 })

      const testEvent: WebSocketEvent = {
        type: 'connected',
        clientId: 'test',
      }

      act(() => {
        MockWebSocket.instances[0].simulateMessage(testEvent)
      })

      // Should use the latest callback (onMessage2)
      expect(onMessage2).toHaveBeenCalled()
      expect(messageCount).toBe(2)
    })
  })
})
