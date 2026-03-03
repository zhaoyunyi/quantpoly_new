/// <reference types="vinxi/types/client" />
import { hydrateRoot } from 'react-dom/client'
import { StartClient } from '@tanstack/react-start'
import { createRouter } from './router'

const router = createRouter()

let _mounted = false

export default function mountClient() {
  // vinxi 可能会通过 handler 的默认导出调用，也可能仅依赖模块副作用。
  // 做成幂等，避免重复 hydrate 造成运行时异常。
  if (_mounted) return
  _mounted = true
  hydrateRoot(document, <StartClient router={router} />)
}

mountClient()
