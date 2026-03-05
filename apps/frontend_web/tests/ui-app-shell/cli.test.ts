// @vitest-environment node
/**
 * UI App Shell — cli.test.ts
 *
 * GIVEN: ui_app_shell 提供 CLI
 * WHEN:  运行 nav probe
 * THEN:  输出可解析 JSON 且包含基础导航项
 */

import { describe, it, expect } from 'vitest'
import { spawnSync } from 'node:child_process'
import path from 'node:path'

describe('ui_app_shell_cli', () => {
  it('given_nav_probe_when_run_then_outputs_nav_items_json', () => {
    const rootDir = path.resolve(import.meta.dirname, '../../../..')
    const cliPath = path.resolve(rootDir, 'libs/ui_app_shell/cli.mjs')

    const result = spawnSync(
      'node',
      [cliPath, '--probe', 'nav'],
      {
        encoding: 'utf-8',
      },
    )

    expect(result.status).toBe(0)
    expect(result.stderr).toBe('')

    const json = JSON.parse(result.stdout)
    expect(json.ok).toBe(true)
    expect(json.probe).toBe('nav')
    expect(Array.isArray(json.items)).toBe(true)
    expect(json.items.length).toBeGreaterThan(0)

    // 基础 IA 校验
    expect(json.items[0].label).toBeDefined()
    expect(json.items[0].path).toMatch(/^\//)
    expect(json.items.map((i: any) => i.path)).toContain('/dashboard')
  })
})
