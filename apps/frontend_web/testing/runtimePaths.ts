import { existsSync, readdirSync } from 'node:fs'
import path from 'node:path'

function candidateRepoRoots(repoRoot: string): string[] {
  const parentDir = path.dirname(repoRoot)
  const roots = [repoRoot]

  for (const entry of readdirSync(parentDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const candidate = path.join(parentDir, entry.name)
    if (candidate === repoRoot) continue
    if (!existsSync(path.join(candidate, 'scripts/run_backend_server.py'))) {
      continue
    }
    roots.push(candidate)
  }

  return roots
}

export function resolveBackendPythonForRepoRoot(repoRoot: string): string {
  const explicit = process.env.PLAYWRIGHT_BACKEND_PYTHON?.trim()
  if (explicit) return explicit

  for (const candidateRoot of candidateRepoRoots(repoRoot)) {
    const pythonPath = path.join(candidateRoot, '.venv', 'bin', 'python')
    if (existsSync(pythonPath)) {
      return pythonPath
    }
  }

  return 'python3'
}

export function resolveBackendPythonCommand(frontendRoot: string): string {
  const repoRoot = path.resolve(frontendRoot, '../..')
  return resolveBackendPythonForRepoRoot(repoRoot)
}
