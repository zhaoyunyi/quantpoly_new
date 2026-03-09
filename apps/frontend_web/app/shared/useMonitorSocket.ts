import { useEffect, useRef, useState } from 'react'

import { getClientConfig, type RiskAlert, type TradingSignal } from '@qp/api-client'
import type { MonitorConnectionState } from '../widgets/monitoring/MonitorConnectionBadge'

type MonitorChannel = 'signals' | 'alerts'

export interface MonitorSocketState {
  connection: MonitorConnectionState
  signals: TradingSignal[]
  alerts: RiskAlert[]
}

function toWsUrl(baseUrl: string, path: string): string {
  const normalized = (baseUrl ?? '').trim().replace(/\/+$/, '')
  if (!normalized) return path

  if (normalized.startsWith('http://')) {
    return `ws://${normalized.slice('http://'.length)}${path}`
  }
  if (normalized.startsWith('https://')) {
    return `wss://${normalized.slice('https://'.length)}${path}`
  }
  if (normalized.startsWith('ws://') || normalized.startsWith('wss://')) {
    return `${normalized}${path}`
  }
  // 兜底：按 host:port 处理
  return `ws://${normalized}${path}`
}

function safeParseJson(value: unknown): unknown {
  if (typeof value !== 'string') return null
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

/**
 * useMonitorSocket
 *
 * - 直连后端 WS `/ws/monitor`（cookie session 鉴权）
 * - subscribe + resync 拉取首个 snapshot
 * - 定时 ping/poll
 * - 断线重连（指数退避，超过阈值标记为 degraded）
 */
export function useMonitorSocket(options?: {
  enabled?: boolean
  channels?: MonitorChannel[]
  pingIntervalMs?: number
  pollIntervalMs?: number
  maxReconnectAttempts?: number
}): MonitorSocketState {
  const enabled = options?.enabled ?? true
  const channels = options?.channels ?? ['signals', 'alerts']
  const pingIntervalMs = options?.pingIntervalMs ?? 15_000
  const pollIntervalMs = options?.pollIntervalMs ?? 5_000
  const maxReconnectAttempts = options?.maxReconnectAttempts ?? 5

  const [connection, setConnection] = useState<MonitorConnectionState>(
    enabled ? 'connecting' : 'offline',
  )
  const [signals, setSignals] = useState<TradingSignal[]>([])
  const [alerts, setAlerts] = useState<RiskAlert[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reconnectAttemptRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!enabled) {
      setConnection('offline')
      return
    }
    if (typeof window === 'undefined') return
    if (typeof WebSocket === 'undefined') {
      setConnection('degraded')
      return
    }

    let cancelled = false

    function clearTimers() {
      if (pingTimerRef.current) clearInterval(pingTimerRef.current)
      pingTimerRef.current = null
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    function closeSocket() {
      const ws = wsRef.current
      wsRef.current = null
      if (ws) {
        try {
          ws.close()
        } catch {
          // ignore
        }
      }
    }

    function scheduleReconnect() {
      if (cancelled) return
      reconnectAttemptRef.current += 1
      if (reconnectAttemptRef.current > maxReconnectAttempts) {
        setConnection('degraded')
        return
      }
      const attempt = reconnectAttemptRef.current
      const delay = Math.min(30_000, 500 * Math.pow(2, attempt - 1))
      reconnectTimerRef.current = setTimeout(() => {
        connect()
      }, delay)
    }

    function connect() {
      if (cancelled) return
      clearTimers()
      closeSocket()

      const baseUrl = getClientConfig().baseUrl
      const wsUrl = toWsUrl(baseUrl, '/ws/monitor')

      setConnection((prev) => (prev === 'degraded' ? 'degraded' : 'connecting'))
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttemptRef.current = 0
        // 订阅 channel + 拉取首个 snapshot
        ws.send(
          JSON.stringify({
            type: 'subscribe',
            payload: { channels },
            timestamp: Date.now(),
          }),
        )
        ws.send(
          JSON.stringify({
            type: 'resync',
            payload: {},
            timestamp: Date.now(),
          }),
        )

        pingTimerRef.current = setInterval(() => {
          try {
            ws.send(
              JSON.stringify({
                type: 'ping',
                payload: {},
                timestamp: Date.now(),
              }),
            )
          } catch {
            // ignore
          }
        }, pingIntervalMs)

        pollTimerRef.current = setInterval(() => {
          try {
            ws.send(
              JSON.stringify({
                type: 'poll',
                payload: {},
                timestamp: Date.now(),
              }),
            )
          } catch {
            // ignore
          }
        }, pollIntervalMs)
      }

      ws.onmessage = (evt) => {
        const parsed =
          typeof evt.data === 'string' ? safeParseJson(evt.data) : evt.data
        if (!parsed || typeof parsed !== 'object') return

        const msg = parsed as { type?: unknown; payload?: unknown; data?: unknown }
        const msgType = String(msg.type ?? '')
        if (msgType === 'monitor.heartbeat') {
          setConnection('connected')
          return
        }

        if (msgType === 'pong') {
          // 当前版本仅用于保持连接活性；如需 RTT/心跳展示，可在此记录时间戳。
          return
        }

        if (msgType === 'signals_update') {
          const payload = (msg.payload as { snapshot?: unknown } | undefined) ?? {}
          const snapshot = Boolean((payload as any).snapshot)
          const data = msg.data as { items?: unknown } | undefined
          const items = Array.isArray(data?.items) ? (data!.items as TradingSignal[]) : []

          setSignals((prev) => {
            if (snapshot) return items
            const seen = new Set(prev.map((x) => x.id))
            return [...prev, ...items.filter((x) => !seen.has(x.id))]
          })
          return
        }

        if (msgType === 'risk_alert') {
          const data = msg.data as { items?: unknown } | undefined
          const items = Array.isArray(data?.items) ? (data!.items as RiskAlert[]) : []
          setAlerts(items)
          return
        }
      }

      ws.onerror = () => {
        if (cancelled) return
        clearTimers()
        setConnection('degraded')
        scheduleReconnect()
      }

      ws.onclose = () => {
        if (cancelled) return
        clearTimers()
        setConnection('degraded')
        scheduleReconnect()
      }
    }

    connect()

    return () => {
      cancelled = true
      clearTimers()
      closeSocket()
    }
  }, [
    enabled,
    channels.join(','),
    pingIntervalMs,
    pollIntervalMs,
    maxReconnectAttempts,
  ])

  return { connection, signals, alerts }
}
