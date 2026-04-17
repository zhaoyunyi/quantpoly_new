import { describe, expect, it } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

const workspaceDir = path.resolve(import.meta.dirname, '../..')
const packageJsonPath = path.join(workspaceDir, 'package.json')
const clientEntryPath = path.join(workspaceDir, 'app/client.tsx')
const serverEntryPath = path.join(workspaceDir, 'app/ssr.tsx')

const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8')) as {
  scripts?: Record<string, string>
  dependencies?: Record<string, string>
  overrides?: Record<string, string>
}

describe('runtime_toolchain', () => {
  it('given_frontend_scripts_when_inspect_then_do_not_boot_via_vinxi', () => {
    expect(packageJson.scripts?.dev).not.toContain('vinxi')
    expect(packageJson.scripts?.build).not.toContain('vinxi')
    expect(packageJson.scripts?.start).not.toContain('vinxi')
  })

  it('given_frontend_dependencies_when_inspect_then_do_not_depend_on_legacy_vinxi_runtime', () => {
    expect(packageJson.dependencies?.vinxi).toBeUndefined()
  })

  it('given_frontend_overrides_when_inspect_then_do_not_pin_obsolete_start_internals', () => {
    expect(packageJson.overrides?.['@tanstack/start-client-core']).toBeUndefined()
    expect(packageJson.overrides?.['@tanstack/start-server-core']).toBeUndefined()
    expect(packageJson.overrides?.['@tanstack/react-start-plugin']).toBeUndefined()
    expect(packageJson.overrides?.['@tanstack/server-functions-plugin']).toBeUndefined()
  })

  it('given_runtime_entries_when_inspect_then_do_not_reference_vinxi_type_shims', () => {
    if (existsSync(clientEntryPath)) {
      const clientEntry = readFileSync(clientEntryPath, 'utf8')
      expect(clientEntry).not.toContain('vinxi/types/client')
    }

    if (existsSync(serverEntryPath)) {
      const serverEntry = readFileSync(serverEntryPath, 'utf8')
      expect(serverEntry).not.toContain('vinxi/types/server')
    }
  })
})
