import type { LargestItem, RootSummary, ScanResponse, ScanStatusResponse, TreeNode } from './types'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function startScan(rootPath: string): Promise<ScanResponse> {
  return fetch('/api/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ root_path: rootPath }),
  }).then((res) => handle<ScanResponse>(res))
}

export function getScanStatus(scanId: number): Promise<ScanStatusResponse> {
  return fetch(`/api/scan/${scanId}/status`).then((res) => handle<ScanStatusResponse>(res))
}

export function getTree(rootPath: string, depth = 4): Promise<TreeNode> {
  const params = new URLSearchParams({ root_path: rootPath, depth: String(depth) })
  return fetch(`/api/tree?${params}`).then((res) => handle<TreeNode>(res))
}

export function listRoots(): Promise<RootSummary[]> {
  return fetch('/api/roots').then((res) => handle<RootSummary[]>(res))
}

export function getLargest(rootPath: string, kind: 'files' | 'dirs', limit = 15): Promise<LargestItem[]> {
  const params = new URLSearchParams({ root_path: rootPath, kind, limit: String(limit) })
  return fetch(`/api/largest?${params}`).then((res) => handle<LargestItem[]>(res))
}
