/**
 * Navigation helpers
 *
 * 统一封装“跳转到另一个路由”的行为，便于测试与替换实现。
 */

export function redirectTo(to: string): void {
  if (typeof window === 'undefined') return
  window.location.assign(to)
}

