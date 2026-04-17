import { useCallback, useEffect, useRef, useState } from 'react'
import type { AppError } from '@qp/api-client'

export interface PollingState<T> {
  loading: boolean
  data: T | null
  error: AppError | null
  reload: () => Promise<void>
  lastUpdatedAt: Date | null
  polling: boolean
}

export function usePolling<T>(
  loader: () => Promise<T>,
  intervalMs: number,
  enabled: boolean,
): PollingState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<AppError | null>(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null)
  const [polling, setPolling] = useState(false)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)
  const initialLoadDone = useRef(false)
  const contextRef = useRef(0)

  const resetState = useCallback(() => {
    setData(null)
    setError(null)
    setLastUpdatedAt(null)
  }, [])

  const invalidateContext = useCallback(() => {
    contextRef.current += 1
  }, [])

  const fetchData = useCallback(
    async (silent: boolean) => {
      const context = contextRef.current
      if (!silent) setLoading(true)
      setError(null)
      try {
        const next = await loader()
        if (mountedRef.current && contextRef.current === context) {
          setData(next)
          setLastUpdatedAt(new Date())
        }
      } catch (err) {
        if (mountedRef.current && contextRef.current === context) {
          setError(err as AppError)
        }
      } finally {
        if (mountedRef.current && !silent && contextRef.current === context) {
          setLoading(false)
        }
      }
    },
    [loader],
  )

  const startInterval = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = setInterval(() => {
      void fetchData(true)
    }, intervalMs)
    setPolling(true)
  }, [fetchData, intervalMs])

  const stopInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setPolling(false)
  }, [])

  const reload = useCallback(async () => {
    await fetchData(initialLoadDone.current)
  }, [fetchData])

  useEffect(() => {
    if (!enabled) {
      invalidateContext()
      stopInterval()
      initialLoadDone.current = false
      resetState()
      setLoading(false)
      return
    }

    invalidateContext()
    resetState()
    initialLoadDone.current = false
    void fetchData(false).then(() => {
      if (mountedRef.current) initialLoadDone.current = true
    })
    startInterval()

    const onVisibility = () => {
      if (document.hidden) {
        stopInterval()
      } else {
        void fetchData(true)
        startInterval()
      }
    }
    document.addEventListener('visibilitychange', onVisibility)

    return () => {
      invalidateContext()
      stopInterval()
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [enabled, fetchData, invalidateContext, resetState, startInterval, stopInterval])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  return { loading, data, error, reload, lastUpdatedAt, polling }
}
