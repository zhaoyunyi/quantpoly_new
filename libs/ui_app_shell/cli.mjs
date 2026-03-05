#!/usr/bin/env node
/**
 * UI App Shell CLI
 *
 * 最小可观测接口：输出 AppShell 的一级导航结构（stdout JSON）。
 *
 * 用法：
 *   node libs/ui_app_shell/cli.mjs --probe nav
 *   node libs/ui_app_shell/cli.mjs --probe nav --nav-path libs/ui_app_shell/src/navigation.tsx
 */

import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const args = process.argv.slice(2)
function getArg(name) {
  const idx = args.indexOf(`--${name}`)
  if (idx === -1 || idx + 1 >= args.length) return undefined
  return args[idx + 1]
}

const probe = getArg('probe') || 'nav'
const navPath = getArg('nav-path') || resolve(__dirname, 'src/navigation.tsx')

function outputJson(obj) {
  process.stdout.write(JSON.stringify(obj, null, 2) + '\n')
}

function parseNavItems(source) {
  // 约束：navigation.tsx 使用对象字面量，并包含 label/path 字段。
  // 这里不执行 TSX，只做最小文本解析，避免引入构建链依赖。
  const items = []
  const re = /label\s*:\s*'([^']+)'[\s\S]*?path\s*:\s*'([^']+)'/g
  let match
  while ((match = re.exec(source)) !== null) {
    items.push({ label: match[1], path: match[2] })
  }
  return items
}

function validateNavItems(items) {
  const invalidPaths = items
    .filter((i) => typeof i.path !== 'string' || !i.path.startsWith('/'))
    .map((i) => i.path)

  const seen = new Set()
  const duplicates = []
  for (const item of items) {
    if (seen.has(item.path)) duplicates.push(item.path)
    seen.add(item.path)
  }

  return {
    invalidPaths,
    duplicatePaths: [...new Set(duplicates)],
  }
}

async function main() {
  if (probe !== 'nav') {
    outputJson({ ok: false, error: `unknown probe: ${probe}` })
    process.exit(1)
  }

  let source
  try {
    source = readFileSync(navPath, 'utf-8')
  } catch (err) {
    outputJson({
      ok: false,
      probe,
      navPath,
      error: 'unable_to_read_nav_source',
      message: err.message,
    })
    process.exit(1)
  }

  const items = parseNavItems(source)
  const { invalidPaths, duplicatePaths } = validateNavItems(items)
  const ok = items.length > 0 && invalidPaths.length === 0 && duplicatePaths.length === 0

  outputJson({
    ok,
    probe: 'nav',
    navPath,
    count: items.length,
    items,
    ...(invalidPaths.length ? { invalidPaths } : {}),
    ...(duplicatePaths.length ? { duplicatePaths } : {}),
  })

  if (!ok) process.exit(1)
}

main()

