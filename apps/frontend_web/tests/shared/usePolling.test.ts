import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePolling } from '../../app/shared/usePolling'

const mockData = { id: 1, name: 'test' }

function createDeferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

function flushPromises() {
  return act(async () => {
    await vi.advanceTimersByTimeAsync(0)
  })
}

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('given_enabled_loader_when_mounted_then_fetches_immediately', async () => {
    const loader = vi.fn(() => Promise.resolve(mockData))

    const { result } = renderHook(() => usePolling(loader, 5000, true))

    await flushPromises()

    expect(loader).toHaveBeenCalledTimes(1)
    expect(result.current.loading).toBe(false)
    expect(result.current.data).toEqual(mockData)
    expect(result.current.error).toBeNull()
  })

  it('given_interval_when_time_passes_then_refetches', async () => {
    const loader = vi.fn(() => Promise.resolve(mockData))

    const { result } = renderHook(() => usePolling(loader, 5000, true))

    await flushPromises()
    expect(loader).toHaveBeenCalledTimes(1)

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })

    expect(loader).toHaveBeenCalledTimes(2)
    expect(result.current.data).toEqual(mockData)
  })

  it('given_tab_hidden_when_polling_then_pauses', async () => {
    const loader = vi.fn(() => Promise.resolve(mockData))

    renderHook(() => usePolling(loader, 5000, true))

    await flushPromises()
    const callCountBeforeHide = loader.mock.calls.length

    act(() => {
      Object.defineProperty(document, 'hidden', {
        configurable: true,
        get: () => true,
      })
      document.dispatchEvent(new Event('visibilitychange'))
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000)
    })

    expect(loader).toHaveBeenCalledTimes(callCountBeforeHide)

    Object.defineProperty(document, 'hidden', {
      configurable: true,
      get: () => false,
    })
  })

  it('given_enabled_false_when_mounted_then_no_fetch', async () => {
    const loader = vi.fn(() => Promise.resolve(mockData))

    renderHook(() => usePolling(loader, 5000, false))

    await flushPromises()

    expect(loader).not.toHaveBeenCalled()
  })

  it('given_successful_fetch_when_complete_then_updates_lastUpdatedAt', async () => {
    const loader = vi.fn(() => Promise.resolve(mockData))

    const { result } = renderHook(() => usePolling(loader, 5000, true))

    expect(result.current.lastUpdatedAt).toBeNull()

    await flushPromises()

    expect(result.current.loading).toBe(false)
    expect(result.current.lastUpdatedAt).toBeInstanceOf(Date)
  })

  it('given_loader_changed_when_next_request_pending_then_clears_stale_data', async () => {
    const firstLoader = vi.fn(() => Promise.resolve(mockData))
    const secondDeferred = createDeferred({ id: 2, name: 'next' })
    const secondLoader = vi.fn(() => secondDeferred.promise)

    const { result, rerender } = renderHook(
      ({ loader }) => usePolling(loader, 5000, true),
      { initialProps: { loader: firstLoader } },
    )

    await flushPromises()

    expect(result.current.data).toEqual(mockData)
    expect(result.current.loading).toBe(false)
    expect(result.current.lastUpdatedAt).toBeInstanceOf(Date)

    rerender({ loader: secondLoader })

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(true)
    expect(result.current.error).toBeNull()
    expect(result.current.lastUpdatedAt).toBeNull()

    secondDeferred.resolve({ id: 2, name: 'next' })
    await flushPromises()

    expect(secondLoader).toHaveBeenCalledTimes(1)
    expect(result.current.data).toEqual({ id: 2, name: 'next' })
    expect(result.current.loading).toBe(false)
    expect(result.current.lastUpdatedAt).toBeInstanceOf(Date)
  })

  it('given_previous_loader_resolves_late_when_loader_changes_then_ignores_stale_response', async () => {
    const firstDeferred = createDeferred(mockData)
    const secondDeferred = createDeferred({ id: 2, name: 'next' })
    const firstLoader = vi.fn(() => firstDeferred.promise)
    const secondLoader = vi.fn(() => secondDeferred.promise)

    const { result, rerender } = renderHook(
      ({ loader }) => usePolling(loader, 5000, true),
      { initialProps: { loader: firstLoader } },
    )

    rerender({ loader: secondLoader })

    firstDeferred.resolve(mockData)
    await flushPromises()

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(true)

    secondDeferred.resolve({ id: 2, name: 'next' })
    await flushPromises()

    expect(result.current.data).toEqual({ id: 2, name: 'next' })
    expect(result.current.loading).toBe(false)
  })
})
