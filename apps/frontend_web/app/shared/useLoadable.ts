import { useCallback, useEffect, useState } from 'react'
import type { AppError } from '@qp/api-client'

export interface LoadableState<T> {
  loading: boolean
  data: T | null
  error: AppError | null
  reload: () => Promise<void>
}

/**
 * useLoadable
 *
 * 极简数据加载 hook：
 * - 首次 mount 自动加载
 * - 支持 reload
 * - 将异常统一映射为 AppError（由 api client 抛出）
 */
export function useLoadable<T>(loader: () => Promise<T>): LoadableState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<AppError | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const next = await loader()
      setData(next)
    } catch (err) {
      setError(err as AppError)
    } finally {
      setLoading(false)
    }
  }, [loader])

  useEffect(() => {
    void reload()
  }, [reload])

  return { loading, data, error, reload }
}

