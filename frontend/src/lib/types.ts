export interface ScanResponse {
  scan_id: number
  root_path: string
  status: 'running' | 'done' | 'error'
}

export interface ScanStatusResponse {
  scan_id: number
  root_path: string
  status: 'running' | 'done' | 'error'
  dirs_visited: number
  dirs_skipped: number
  files_stated: number
  elapsed_seconds: number
  error_message: string | null
}

export interface TreeNode {
  path: string
  name: string
  size: number
  is_dir: boolean
  mtime: number | null
  last_scanned: number
  error: string | null
  children: TreeNode[]
}

export interface LargestItem {
  path: string
  name: string
  size: number
  is_dir: boolean
}

export interface RootSummary {
  root_path: string
  last_scanned: number | null
  total_size: number | null
  status: string
}
