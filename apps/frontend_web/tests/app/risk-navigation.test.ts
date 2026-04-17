/**
 * App Shell navigation contract test
 *
 * Ensures /trading/analytics is reachable via the trading sub-menu.
 */

import { describe, expect, it } from 'vitest'
import { NAV_ITEMS } from '@qp/shell'

describe('app_shell_navigation', () => {
  it('given_trading_nav_item_when_resolve_children_then_contains_analytics_path', () => {
    const tradingItem = NAV_ITEMS.find((item) => item.label === '\u4EA4\u6613\u8D26\u6237')

    expect(tradingItem).toBeDefined()
    expect(tradingItem?.path).toBe('/trading')

    const analyticsChild = tradingItem?.children?.find(
      (child) => child.path === '/trading/analytics',
    )
    expect(analyticsChild).toBeDefined()
    expect(analyticsChild?.label).toBe('\u5206\u6790\u62A5\u8868')
  })
})
