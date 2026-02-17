import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import fs from 'node:fs'

export interface SnapshotResponse {
  status: number
  json: unknown
}

export interface BackendSnapshot {
  token: string
  responses: {
    users_me: SnapshotResponse
    strategies: SnapshotResponse
    backtests: SnapshotResponse
    trading_accounts: SnapshotResponse
    monitor_summary: SnapshotResponse
    unauth_strategies: SnapshotResponse
  }
}

function resolveRepoRoot(fromDir: string): string {
  // tests/contract -> tests -> frontend_web -> apps -> repo_root
  return path.resolve(fromDir, '../../../../')
}

function resolvePythonBin(repoRoot: string): string {
  const venvPython = path.join(repoRoot, '.venv', 'bin', 'python')
  if (fs.existsSync(venvPython)) return venvPython
  return 'python3'
}

export function loadBackendSnapshot(): BackendSnapshot {
  const here = path.dirname(fileURLToPath(import.meta.url))
  const repoRoot = resolveRepoRoot(here)
  const scriptPath = path.join(here, 'backend_snapshot.py')

  const python = resolvePythonBin(repoRoot)
  const stdout = execFileSync(python, [scriptPath], {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
    },
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024,
    timeout: 60_000,
  })

  return JSON.parse(stdout) as BackendSnapshot
}

