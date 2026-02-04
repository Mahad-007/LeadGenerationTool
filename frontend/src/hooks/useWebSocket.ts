import { useState, useEffect, useCallback, useRef } from 'react'
import type { WebSocketEvent } from '@/types'

export interface UseWebSocketOptions {
  url: string
  enabled?: boolean
  onMessage?: (event: WebSocketEvent) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectAttempts?: number
  reconnectInterval?: number
}

export interface UseWebSocketReturn {
  isConnected: boolean
  lastMessage: WebSocketEvent | null
  send: (data: unknown) => void
  disconnect: () => void
  reconnect: () => void
}

export function useWebSocket({
  url,
  enabled = true,
  onMessage,
  onOpen,
  onClose,
  onError,
  reconnectAttempts = 3,
  reconnectInterval = 3000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketEvent | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isManualDisconnectRef = useRef(false)

  // Use refs for callbacks to avoid stale closures
  const onMessageRef = useRef(onMessage)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)
  const onErrorRef = useRef(onError)

  // Keep refs updated with latest callbacks
  useEffect(() => {
    onMessageRef.current = onMessage
    onOpenRef.current = onOpen
    onCloseRef.current = onClose
    onErrorRef.current = onError
  }, [onMessage, onOpen, onClose, onError])

  const connect = useCallback(() => {
    if (!enabled) return

    // Close existing connection if any (prevents memory leak)
    if (wsRef.current) {
      const existingWs = wsRef.current
      wsRef.current = null
      if (existingWs.readyState === WebSocket.OPEN || existingWs.readyState === WebSocket.CONNECTING) {
        existingWs.close()
      }
    }

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      reconnectCountRef.current = 0
      onOpenRef.current?.()
    }

    ws.onclose = () => {
      setIsConnected(false)
      onCloseRef.current?.()

      // Only attempt reconnection if not manual disconnect and still enabled
      if (!isManualDisconnectRef.current && enabled && reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current += 1
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, reconnectInterval)
      }
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketEvent
        setLastMessage(data)
        onMessageRef.current?.(data)
      } catch {
        // Use console.warn for non-critical parse errors
        console.warn('Failed to parse WebSocket message:', event.data)
      }
    }

    ws.onerror = (error) => {
      onErrorRef.current?.(error)
    }
  }, [url, enabled, reconnectAttempts, reconnectInterval])

  const disconnect = useCallback(() => {
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Mark as manual disconnect to prevent auto-reconnection
    isManualDisconnectRef.current = true
    reconnectCountRef.current = reconnectAttempts

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [reconnectAttempts])

  const reconnect = useCallback(() => {
    // Clear pending reconnection timeout first
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close existing connection synchronously
    if (wsRef.current) {
      const existingWs = wsRef.current
      wsRef.current = null
      // Remove onclose handler to prevent auto-reconnect from firing
      existingWs.onclose = null
      existingWs.close()
    }

    // Reset state for fresh connection
    isManualDisconnectRef.current = false
    reconnectCountRef.current = 0
    setIsConnected(false)

    // Create new connection
    connect()
  }, [connect])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  // Connect on mount/url change, cleanup on unmount
  useEffect(() => {
    isManualDisconnectRef.current = false
    reconnectCountRef.current = 0
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
      if (wsRef.current) {
        wsRef.current.onclose = null // Prevent reconnect on cleanup
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  return {
    isConnected,
    lastMessage,
    send,
    disconnect,
    reconnect,
  }
}
