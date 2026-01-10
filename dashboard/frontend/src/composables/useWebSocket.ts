import { ref, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import type { WSEvent, Memory } from '@/types'
import { logger } from '@/utils/logger'

export function useWebSocket() {
  const store = useDashboardStore()
  const ws = ref<WebSocket | null>(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  let pingInterval: ReturnType<typeof setInterval> | null = null

  function connect() {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    logger.log('[WS] Connecting to:', wsUrl)
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      logger.log('[WS] Connected')
      store.setConnected(true)
      reconnectAttempts.value = 0

      // Start ping interval to keep connection alive
      pingInterval = setInterval(() => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          ws.value.send('ping')
        }
      }, 30000)
    }

    ws.value.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data)
        handleEvent(data)
      } catch (e) {
        logger.error('[WS] Failed to parse message:', e)
      }
    }

    ws.value.onclose = () => {
      logger.log('[WS] Disconnected')
      store.setConnected(false)
      cleanup()
      attemptReconnect()
    }

    ws.value.onerror = (error) => {
      logger.error('[WS] Error:', error)
    }
  }

  function handleEvent(event: WSEvent) {
    logger.log('[WS] Event:', event.event_type, event.data)

    switch (event.event_type) {
      case 'connected':
        logger.log('[WS] Connection confirmed, client ID:', event.data.client_id)
        break

      case 'pong':
        // Ping response, connection is alive
        break

      case 'memory_created':
        store.handleMemoryCreated(event.data as unknown as Memory)
        break

      case 'memory_updated':
        store.handleMemoryUpdated(event.data as unknown as Memory)
        break

      case 'memory_deleted':
        store.handleMemoryDeleted(event.data.id as string)
        break

      case 'database_changed':
        store.handleDatabaseChanged()
        break

      default:
        logger.log('[WS] Unknown event type:', event.event_type)
    }
  }

  function attemptReconnect() {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      logger.log('[WS] Max reconnect attempts reached')
      return
    }

    reconnectAttempts.value++
    logger.log(`[WS] Reconnecting (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})...`)

    reconnectTimeout = setTimeout(() => {
      connect()
    }, reconnectDelay)
  }

  function disconnect() {
    cleanup()
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    store.setConnected(false)
  }

  function cleanup() {
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connect,
    disconnect,
    isConnected: store.isConnected,
  }
}
