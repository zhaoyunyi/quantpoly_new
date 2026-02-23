/**
 * App Shell — 一级导航配置
 *
 * 导航项与路径对齐 UISpec 8.1 信息架构。
 */

import type { ReactNode } from 'react'

export interface NavItem {
  /** 导航标签 */
  label: string
  /** 路由路径 */
  path: string
  /** SVG 图标（24x24），作为 <svg> 的 children 渲染 */
  icon: ReactNode
}

/**
 * 一级导航项。
 * 顺序对齐 UISpec 8.1：仪表盘 · 策略管理 · 回测中心 · 交易账户 · 风控中心 · 实时监控 · 用户中心
 */
export const NAV_ITEMS: NavItem[] = [
  {
    label: '仪表盘',
    path: '/dashboard',
    icon: (
      <path
        d="M4 13h6a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1zm0 8h6a1 1 0 0 0 1-1v-4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1zm10 0h6a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1zm0-18v4a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    ),
  },
  {
    label: '策略管理',
    path: '/strategies',
    icon: (
      <path
        d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 5h6m-3 7v4m-2-2h4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    ),
  },
  {
    label: '回测中心',
    path: '/backtests',
    icon: (
      <>
        <path
          d="M3 12l2-2m0 0l7-7 7 7m-9-5v12m4-8h4a2 2 0 0 1 2 2v6"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <polyline
          points="3,17 8,12 13,16 21,8"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </>
    ),
  },
  {
    label: '交易账户',
    path: '/trading',
    icon: (
      <>
        <rect
          x="3"
          y="5"
          width="18"
          height="14"
          rx="2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path
          d="M3 10h18M7 15h2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </>
    ),
  },
  {
    label: '风控中心',
    path: '/trading/analytics',
    icon: (
      <>
        <path
          d="M12 2l8 4v6c0 5.5-3.8 10.7-8 12-4.2-1.3-8-6.5-8-12V6l8-4z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M12 8v4m0 4h.01"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </>
    ),
  },
  {
    label: '实时监控',
    path: '/monitor',
    icon: (
      <path
        d="M5 12h2l3-7 4 14 3-7h2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
  {
    label: '用户中心',
    path: '/settings',
    icon: (
      <>
        <circle
          cx="12"
          cy="12"
          r="3"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path
          d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </>
    ),
  },
]
