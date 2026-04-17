import { useEffect } from 'react'

export function useHotkey(
  key: string,
  modifier: 'meta' | 'ctrl' | 'meta-or-ctrl',
  callback: () => void,
) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() !== key.toLowerCase()) return
      const modMatch =
        modifier === 'meta'
          ? e.metaKey
          : modifier === 'ctrl'
            ? e.ctrlKey
            : e.metaKey || e.ctrlKey
      if (!modMatch) return
      e.preventDefault()
      callback()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [key, modifier, callback])
}
