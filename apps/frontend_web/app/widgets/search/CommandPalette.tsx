import { useState, useMemo, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Dialog, TextField } from '@qp/ui'
import { NAV_ITEMS } from '@qp/shell'

export interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  const results = useMemo(() => {
    if (!query.trim()) return NAV_ITEMS
    const q = query.toLowerCase()
    return NAV_ITEMS.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.path.toLowerCase().includes(q),
    )
  }, [query])

  const handleSelect = useCallback(
    (path: string) => {
      onOpenChange(false)
      setQuery('')
      void navigate({ to: path })
    },
    [navigate, onOpenChange],
  )

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        onOpenChange(o)
        if (!o) setQuery('')
      }}
      title="快速导航"
      description="输入页面名称快速跳转"
    >
      <div className="flex flex-col gap-md">
        <TextField
          label=""
          placeholder="搜索页面..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <ul className="flex flex-col gap-xs max-h-64 overflow-y-auto">
          {results.length === 0 ? (
            <li className="text-caption text-text-muted text-center py-md">
              未找到匹配页面
            </li>
          ) : (
            results.map((item) => (
              <li key={item.path}>
                <button
                  type="button"
                  onClick={() => handleSelect(item.path)}
                  className="w-full flex items-center gap-sm px-sm py-xs rounded-sm text-body text-left hover:bg-bg-subtle transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40"
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    className="shrink-0 text-text-muted"
                    aria-hidden="true"
                  >
                    {item.icon}
                  </svg>
                  <span>{item.label}</span>
                  <span className="ml-auto text-caption text-text-muted">{item.path}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </Dialog>
  )
}
