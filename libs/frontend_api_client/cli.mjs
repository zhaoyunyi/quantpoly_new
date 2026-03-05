#!/usr/bin/env node
/**
 * Frontend API Client CLI
 *
 * 健康检查与 CORS 探测工具，输出 JSON。
 *
 * 用法：
 *   node cli.mjs --backend http://localhost:8000
 *   node cli.mjs --backend http://localhost:8000 --probe cors --origin http://localhost:3000
 */

const args = process.argv.slice(2)

function getArg(name) {
  const idx = args.indexOf(`--${name}`)
  if (idx === -1 || idx + 1 >= args.length) return undefined
  return args[idx + 1]
}

const backend = getArg('backend') || 'http://localhost:8000'
const probe = getArg('probe') || 'health'
const origin = getArg('origin') || 'http://localhost:3000'

async function probeHealth() {
  try {
    const res = await fetch(`${backend}/health`, {
      headers: { Accept: 'application/json' },
    })
    const json = await res.json()
    return {
      probe: 'health',
      backend,
      status: res.status,
      ok: res.ok,
      body: json,
    }
  } catch (err) {
    return {
      probe: 'health',
      backend,
      ok: false,
      error: err.message,
    }
  }
}

async function probeCors() {
  try {
    const res = await fetch(`${backend}/health`, {
      method: 'OPTIONS',
      headers: {
        Origin: origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type',
      },
    })
    const corsHeaders = {
      'access-control-allow-origin':
        res.headers.get('access-control-allow-origin'),
      'access-control-allow-credentials':
        res.headers.get('access-control-allow-credentials'),
      'access-control-allow-methods':
        res.headers.get('access-control-allow-methods'),
      'access-control-allow-headers':
        res.headers.get('access-control-allow-headers'),
    }
    // Cookie session（credentials: include）安全约束：
    // - allow-origin 必须精确匹配 Origin（禁止 "*"）
    // - allow-credentials 必须为 true
    const allowOrigin = corsHeaders['access-control-allow-origin']
    const allowCreds = corsHeaders['access-control-allow-credentials']
    const insecureWildcard = allowOrigin === '*'
    const allowed = allowOrigin === origin && allowCreds === 'true'
    return {
      probe: 'cors',
      backend,
      origin,
      ok: res.ok,
      status: res.status,
      allowed,
      insecureWildcard,
      headers: corsHeaders,
    }
  } catch (err) {
    return {
      probe: 'cors',
      backend,
      origin,
      allowed: false,
      error: err.message,
    }
  }
}

async function main() {
  let result
  if (probe === 'cors') {
    result = await probeCors()
  } else {
    result = await probeHealth()
  }

  const output = JSON.stringify(result, null, 2)
  process.stdout.write(output + '\n')

  if (!result.ok && !result.allowed) {
    process.exit(1)
  }
}

main()
