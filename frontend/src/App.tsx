import { useEffect, useState } from 'react'
import './App.css'
import { Breadcrumb } from './components/Breadcrumb'
import { BreakdownBar } from './components/BreakdownBar'
import { LargestList } from './components/LargestList'
import { RootsList } from './components/RootsList'
import { Treemap } from './components/Treemap'
import { formatBytes } from './lib/format'
import { getLargest, getScanStatus, getTree, listRoots, startScan } from './lib/api'
import type { LargestItem, RootSummary, ScanStatusResponse, TreeNode } from './lib/types'

const HOME_PATH = '~'

function App() {
  const [pathInput, setPathInput] = useState('')
  const [scanRoot, setScanRoot] = useState<string | null>(null)
  const [currentPath, setCurrentPath] = useState<string | null>(null)
  const [status, setStatus] = useState<ScanStatusResponse | null>(null)
  const [tree, setTree] = useState<TreeNode | null>(null)
  const [largestFiles, setLargestFiles] = useState<LargestItem[]>([])
  const [largestDirs, setLargestDirs] = useState<LargestItem[]>([])
  const [roots, setRoots] = useState<RootSummary[]>([])
  const [error, setError] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    refreshRoots()
  }, [])

  async function refreshRoots() {
    try {
      setRoots(await listRoots())
    } catch {
      // landing page is best-effort; a failed roots fetch shouldn't block scanning
    }
  }

  async function loadTree(path: string) {
    try {
      setTree(await getTree(path))
      setCurrentPath(path)
      // Best-effort: largest-items ranking shouldn't block the treemap if it fails.
      const [files, dirs] = await Promise.all([
        getLargest(path, 'files').catch(() => []),
        getLargest(path, 'dirs').catch(() => []),
      ])
      setLargestFiles(files)
      setLargestDirs(dirs)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  async function runScan(path: string) {
    setError(null)
    setScanning(true)
    setStatus(null)
    try {
      const { scan_id } = await startScan(path)
      await pollUntilDone(scan_id)
      setScanRoot(path)
      await loadTree(path)
      await refreshRoots()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setScanning(false)
    }
  }

  async function pollUntilDone(scanId: number) {
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const s = await getScanStatus(scanId)
      setStatus(s)
      if (s.status === 'done' || s.status === 'error') return
      await new Promise((r) => setTimeout(r, 200))
    }
  }

  function handleSelectRoot(rootPath: string) {
    setScanRoot(rootPath)
    loadTree(rootPath)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>{import.meta.env.VITE_APP_TITLE || 'Disk Space Analysis'}</h1>
      </header>

      <main className="app-main">
        <div className="card">
          <input
            type="text"
            value={pathInput}
            onChange={(e) => setPathInput(e.target.value)}
            placeholder="/Users/you/Downloads"
            style={{ width: '24rem' }}
          />
          <button onClick={() => runScan(pathInput)} disabled={!pathInput || scanning}>
            {scanning ? 'Scanning…' : 'Scan'}
          </button>
          <button onClick={() => runScan(HOME_PATH)} disabled={scanning}>
            Scan Home (~)
          </button>
          {scanRoot && (
            <button onClick={() => runScan(scanRoot)} disabled={scanning}>
              Rescan
            </button>
          )}
        </div>

        {error && <p style={{ color: 'red' }}>{error}</p>}

        {status && status.status === 'running' && (
          <p>
            Scanning… {status.dirs_visited} dirs visited ({status.dirs_skipped} skipped),{' '}
            {status.files_stated} files checked
          </p>
        )}
        {status && status.status === 'error' && <p style={{ color: 'red' }}>Scan failed: {status.error_message}</p>}

        {scanRoot && currentPath && tree && (
          <div>
            <Breadcrumb scanRoot={scanRoot} currentPath={currentPath} onNavigate={loadTree} />
            <p>{formatBytes(tree.size)} total</p>
            <BreakdownBar root={tree} />
            <Treemap root={tree} onDrillDown={loadTree} />
            <LargestList scanRoot={scanRoot} files={largestFiles} dirs={largestDirs} onDrillDown={loadTree} />
          </div>
        )}

        <RootsList roots={roots} onSelect={handleSelectRoot} />
      </main>
    </div>
  )
}

export default App
