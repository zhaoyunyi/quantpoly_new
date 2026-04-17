/**
 * App Shell — redirect helper
 *
 * 统一封装“跳转”行为，便于测试中替换实现，避免直接触发 JSDOM 导航异常。
 */

function isInternalPath(to: string): boolean {
  return to.startsWith('/') && !to.startsWith('//')
}

export function redirectTo(to: string): void {
  if (typeof window === 'undefined') return
  if (isInternalPath(to)) {
    window.history.pushState({}, '', to)
    window.dispatchEvent(new PopStateEvent('popstate'))
    return
  }
  window.location.assign(to)
}
