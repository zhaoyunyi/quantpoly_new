#!/usr/bin/env node

/**
 * validate-tokens.mjs
 *
 * 校验 design-tokens/tokens.json 与 app/styles/app.css 的同步性。
 * 可选 --lint 模式扫描业务代码中的硬编码颜色。
 *
 * Usage:
 *   node scripts/validate-tokens.mjs          # 校验 tokens ↔ CSS 同步
 *   node scripts/validate-tokens.mjs --lint    # 扫描硬编码颜色
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { resolve, join, extname } from 'node:path'

const ROOT = resolve(import.meta.dirname, '..')
const TOKENS_PATH = join(ROOT, 'design-tokens/tokens.json')
const CSS_PATH = join(ROOT, 'app/styles/app.css')

const isLint = process.argv.includes('--lint')

/* ─── helpers ─── */

function loadTokens() {
  const raw = JSON.parse(readFileSync(TOKENS_PATH, 'utf8'))
  const names = []
  function walk(obj, prefix) {
    for (const [k, v] of Object.entries(obj)) {
      if (k.startsWith('$')) continue
      if (v && typeof v === 'object' && '$type' in v) {
        names.push(prefix ? `${prefix}-${k}` : k)
      } else if (v && typeof v === 'object') {
        walk(v, prefix ? `${prefix}-${k}` : k)
      }
    }
  }
  walk(raw, '')
  return names
}

function extractCssVars(css) {
  const vars = new Set()
  for (const m of css.matchAll(/--([a-z][a-z0-9-]*)\s*:/g)) {
    vars.add(m[1])
  }
  return vars
}

/* ─── validate: tokens ↔ CSS sync ─── */

function validate() {
  const tokenNames = loadTokens()
  const css = readFileSync(CSS_PATH, 'utf8')
  const cssVars = extractCssVars(css)

  let errors = 0

  // token 分类前缀映射到 CSS 变量前缀
  const PREFIX_MAP = {
    'color-': 'color-',
    'radius-': 'radius-',
    'shadow-': 'shadow-',
    'spacing-': 'space-',
    'transition-': 'transition-',
  }

  for (const name of tokenNames) {
    // 跳过 typography tokens（font-sans 等在 @theme 中直接定义）
    if (name.startsWith('typography-')) continue

    let cssName = name
    for (const [from, to] of Object.entries(PREFIX_MAP)) {
      if (name.startsWith(from)) {
        cssName = to + name.slice(from.length)
        break
      }
    }

    if (!cssVars.has(cssName)) {
      console.error(`MISSING in CSS: --${cssName} (token: ${name})`)
      errors++
    }
  }

  if (errors === 0) {
    console.log(`✓ All ${tokenNames.length} tokens are synced with CSS.`)
  } else {
    console.error(`\n✗ ${errors} token(s) missing from CSS.`)
    process.exit(1)
  }
}

/* ─── lint: scan for hardcoded colors ─── */

const HEX_RE = /#[0-9a-fA-F]{3,8}\b/g
const RGB_RE = /\brgba?\s*\(/g
const HSL_RE = /\bhsla?\s*\(/g

const IGNORE_DIRS = ['node_modules', '.next', 'dist', 'build', '.git', 'design-tokens', 'scripts']
const SCAN_EXTS = new Set(['.tsx', '.ts', '.css'])

function* walkFiles(dir) {
  for (const entry of readdirSync(dir)) {
    if (IGNORE_DIRS.includes(entry)) continue
    const full = join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) yield* walkFiles(full)
    else if (SCAN_EXTS.has(extname(full))) yield full
  }
}

function lint() {
  let hits = 0
  const appDir = join(ROOT, 'app')

  for (const file of walkFiles(appDir)) {
    const content = readFileSync(file, 'utf8')
    const lines = content.split('\n')

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      // skip CSS variable definitions (they're allowed)
      if (line.includes('--color-') || line.includes('--shadow-')) continue
      // skip comments
      if (line.trim().startsWith('//') || line.trim().startsWith('/*') || line.trim().startsWith('*')) continue

      for (const re of [HEX_RE, RGB_RE, HSL_RE]) {
        re.lastIndex = 0
        let m
        while ((m = re.exec(line)) !== null) {
          const rel = file.replace(ROOT + '/', '')
          console.warn(`${rel}:${i + 1} — hardcoded color: ${m[0]}`)
          hits++
        }
      }
    }
  }

  if (hits === 0) {
    console.log('✓ No hardcoded colors found in app/ source files.')
  } else {
    console.warn(`\n⚠ ${hits} hardcoded color(s) found. Use Design Tokens instead.`)
    process.exit(1)
  }
}

/* ─── main ─── */

if (isLint) {
  lint()
} else {
  validate()
}
