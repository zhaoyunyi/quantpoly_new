import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const workspaceDir = path.resolve(import.meta.dirname, '../..')
const playwrightConfigPath = path.join(workspaceDir, 'playwright.config.ts')
const playwrightConfig = readFileSync(playwrightConfigPath, 'utf8')

describe('playwright_runtime_config', () => {
  it('given_backend_web_server_when_inspect_then_does_not_hardcode_workspace_local_venv_only', () => {
    expect(playwrightConfig).not.toContain('../../.venv/bin/python')
  })

  it('given_backend_web_server_when_inspect_then_uses_shared_python_resolution_helper', () => {
    expect(playwrightConfig).toContain('resolveBackendPythonCommand')
  })
})
