import { describe, it, expect } from 'vitest'
import {
  formatInt,
  formatCurrency,
  formatPercent,
  formatDate,
  formatMetric,
} from '../../app/shared/format'

describe('format utilities', () => {
  it('given_number_when_formatInt_then_returns_zh_CN_locale', () => {
    const result = formatInt(1234567)
    // zh-CN locale 使用千分位分隔
    expect(result).toMatch(/1.*234.*567/)
  })

  it('given_number_when_formatCurrency_then_returns_2_decimals', () => {
    const result = formatCurrency(1234.5)
    expect(result).toMatch(/\.50$/)
  })

  it('given_ratio_when_formatPercent_then_returns_percentage', () => {
    expect(formatPercent(0.1234)).toBe('12.34%')
  })

  it('given_NaN_when_formatInt_then_returns_zero', () => {
    expect(formatInt(NaN)).toBe('0')
  })

  it('given_NaN_when_formatCurrency_then_returns_zero', () => {
    expect(formatCurrency(NaN)).toBe('0.00')
  })

  it('given_NaN_when_formatPercent_then_returns_zero_percent', () => {
    expect(formatPercent(NaN)).toBe('0.00%')
  })

  it('given_iso_string_when_formatDate_then_returns_zh_CN', () => {
    const result = formatDate('2026-01-01T00:00:00Z')
    expect(typeof result).toBe('string')
    expect(result.length).toBeGreaterThan(0)
  })

  it('given_number_when_formatMetric_then_returns_up_to_4_decimals', () => {
    expect(formatMetric(1234.56789)).toMatch(/1.*234\.567/)
  })

  it('given_null_when_formatMetric_then_returns_dash', () => {
    expect(formatMetric(null)).toBe('-')
    expect(formatMetric(undefined)).toBe('-')
  })

  it('given_string_when_formatMetric_then_returns_dash_for_non_numeric', () => {
    expect(formatMetric('abc')).toBe('-')
  })
})
