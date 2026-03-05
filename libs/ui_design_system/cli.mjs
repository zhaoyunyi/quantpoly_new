#!/usr/bin/env node
/**
 * UI Design System — Tokens 校验 CLI
 *
 * 读取 app.css 中的 @theme {} 块，提取 tokens 列表并输出 JSON。
 * 对缺失的必需 token 返回非 0 exit code。
 *
 * 用法：
 *   node cli.mjs [--css-path ../../apps/frontend_web/app/styles/app.css]
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

const cssPath = getArg('css-path') ||
  resolve(__dirname, '../../apps/frontend_web/app/styles/app.css')

/* ─── 必需 Tokens ─── */
const REQUIRED_TOKENS = [
  // 品牌色
  '--color-primary-900',
  '--color-primary-700',
  '--color-primary-500',
  '--color-secondary-500',
  '--color-secondary-300',
  // 背景
  '--color-bg-page',
  '--color-bg-card',
  '--color-bg-subtle',
  // 文本
  '--color-text-primary',
  '--color-text-secondary',
  '--color-text-muted',
  // 状态
  '--color-state-up',
  '--color-state-down',
  '--color-state-risk',
  '--color-state-disabled',
  // 图表
  '--color-chart-primary',
  '--color-chart-secondary',
  '--color-chart-grid',
  '--color-chart-axis',
  // 字体
  '--font-sans',
  '--font-mono',
  // 字号
  '--text-h1',
  '--text-h2',
  '--text-h3',
  '--text-body',
  '--text-caption',
  // 间距
  '--spacing-xs',
  '--spacing-sm',
  '--spacing-md',
  '--spacing-lg',
  '--spacing-xl',
  '--spacing-2xl',
  // 圆角
  '--radius-sm',
  '--radius-md',
  // 阴影
  '--shadow-card',
  // 过渡
  '--transition-base',
]

/* ─── 主逻辑 ─── */

let css
try {
  css = readFileSync(cssPath, 'utf-8')
} catch (err) {
  const result = {
    ok: false,
    error: `无法读取 CSS 文件: ${cssPath}`,
    message: err.message,
  }
  process.stdout.write(JSON.stringify(result, null, 2) + '\n')
  process.exit(1)
}

// 提取 @theme { ... } 块
const themeMatch = css.match(/@theme\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}/s)
if (!themeMatch) {
  const result = {
    ok: false,
    error: '未找到 @theme {} 块',
    path: cssPath,
  }
  process.stdout.write(JSON.stringify(result, null, 2) + '\n')
  process.exit(1)
}

const themeBlock = themeMatch[1]

// 解析所有 token
const tokenRegex = /(--[\w-]+)\s*:\s*([^;]+);/g
const tokens = {}
let match
while ((match = tokenRegex.exec(themeBlock)) !== null) {
  tokens[match[1]] = match[2].trim()
}

// 校验必需 tokens
const missing = REQUIRED_TOKENS.filter((t) => !(t in tokens))
const ok = missing.length === 0

const result = {
  ok,
  path: cssPath,
  tokenCount: Object.keys(tokens).length,
  tokens,
  ...(missing.length > 0 ? { missing } : {}),
}

process.stdout.write(JSON.stringify(result, null, 2) + '\n')

if (!ok) {
  process.exit(1)
}
