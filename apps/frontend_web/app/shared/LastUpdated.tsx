/**
 * LastUpdated — 最后更新时间 + 刷新按钮
 *
 * 纯展示组件，不持有数据加载逻辑。
 */

import { Button } from '@qp/ui'

export interface LastUpdatedProps {
  lastUpdatedAt: Date | null
  onRefresh: () => void
  loading?: boolean
}

function RefreshIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M13.5 2.5v4h-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M2.5 8a5.5 5.5 0 0 1 9.35-3.5L13.5 6.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M2.5 13.5v-4h4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13.5 8a5.5 5.5 0 0 1-9.35 3.5L2.5 9.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function LastUpdated({
  lastUpdatedAt,
  onRefresh,
  loading = false,
}: LastUpdatedProps) {
  const timeText = lastUpdatedAt
    ? `最后更新: ${lastUpdatedAt.toLocaleTimeString('zh-CN')}`
    : '加载中...'

  return (
    <div className="inline-flex items-center gap-sm">
      <span className="text-caption text-text-muted">{timeText}</span>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRefresh}
        disabled={loading}
        aria-label="刷新"
      >
        <RefreshIcon />
      </Button>
    </div>
  )
}
