import { useEffect, useRef } from 'react'

export interface Shortcut {
  keys: string
  description: string
  action: () => void
}

export function useHotkeys(shortcuts: Shortcut[]) {
  const sequenceRef = useRef('')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

      // Handle modifier shortcuts (Cmd+K, Cmd+/)
      if (e.metaKey || e.ctrlKey) {
        const key = `${e.metaKey ? 'cmd' : 'ctrl'}+${e.key.toLowerCase()}`
        const match = shortcuts.find((s) => s.keys === key)
        if (match) {
          e.preventDefault()
          match.action()
          return
        }
      }

      // Handle sequence shortcuts (g d, g t, etc.)
      if (timerRef.current) clearTimeout(timerRef.current)
      sequenceRef.current += e.key.toLowerCase()

      const match = shortcuts.find((s) => s.keys === sequenceRef.current)
      if (match) {
        e.preventDefault()
        match.action()
        sequenceRef.current = ''
        return
      }

      // Check if any shortcut starts with current sequence
      const hasPrefix = shortcuts.some((s) => s.keys.startsWith(sequenceRef.current))
      if (hasPrefix) {
        timerRef.current = setTimeout(() => {
          sequenceRef.current = ''
        }, 500)
      } else {
        sequenceRef.current = ''
      }
    }

    document.addEventListener('keydown', handler)
    return () => {
      document.removeEventListener('keydown', handler)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [shortcuts])
}

export function getShortcutLabel(keys: string): string {
  return keys
    .replace('cmd+', '⌘')
    .replace('ctrl+', 'Ctrl+')
    .toUpperCase()
}
