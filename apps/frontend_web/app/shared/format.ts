/**
 * 通用格式化工具函数
 *
 * 统一替代 dashboard / monitor / backtests / strategies 中散落的格式化逻辑。
 * 纯函数，无 React 依赖。
 */

/** 整数格式化（zh-CN locale，千分位） */
export function formatInt(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return Math.trunc(value).toLocaleString('zh-CN')
}

/** 货币格式化（保留 2 位小数） */
export function formatCurrency(value: number): string {
  if (!Number.isFinite(value)) return '0.00'
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/** 百分比格式化（乘 100 后保留 2 位小数） */
export function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return '0.00%'
  return (value * 100).toFixed(2) + '%'
}

/** 通用指标格式化（保留最多 4 位小数，null/undefined → "-"） */
export function formatMetric(val: unknown): string {
  if (val === null || val === undefined) return '-'
  const num = Number(val)
  if (!Number.isFinite(num)) return '-'
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 4 })
}

/** ISO 日期字符串 → zh-CN 本地化字符串 */
export function formatDate(isoStr: string): string {
  return new Date(isoStr).toLocaleString('zh-CN')
}
