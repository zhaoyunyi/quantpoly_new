/**
 * Navigation helpers
 *
 * 统一封装“跳转到另一个路由”的行为，便于测试与替换实现。
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
