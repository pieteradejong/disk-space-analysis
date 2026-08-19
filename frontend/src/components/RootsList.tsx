import { formatBytes } from '../lib/format'
import type { RootSummary } from '../lib/types'

interface RootsListProps {
  roots: RootSummary[]
  onSelect: (rootPath: string) => void
}

export function RootsList({ roots, onSelect }: RootsListProps) {
  if (roots.length === 0) return null

  return (
    <div className="roots-list">
      <h2>Previously scanned</h2>
      <ul>
        {roots.map((r) => (
          <li key={r.root_path}>
            <button onClick={() => onSelect(r.root_path)}>
              {r.root_path} — {r.total_size != null ? formatBytes(r.total_size) : '?'} ({r.status})
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
