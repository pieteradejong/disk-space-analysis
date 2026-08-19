import { formatBytes } from '../lib/format'
import type { LargestItem } from '../lib/types'

interface LargestListProps {
  scanRoot: string
  files: LargestItem[]
  dirs: LargestItem[]
  onDrillDown: (path: string) => void
}

function relativePath(path: string, scanRoot: string): string {
  if (path === scanRoot) return path
  return path.startsWith(scanRoot) ? path.slice(scanRoot.length + 1) : path
}

function ItemTable({
  title,
  items,
  scanRoot,
  onDrillDown,
}: {
  title: string
  items: LargestItem[]
  scanRoot: string
  onDrillDown: (path: string) => void
}) {
  if (items.length === 0) return null

  return (
    <div className="largest-table">
      <h3>{title}</h3>
      <table>
        <tbody>
          {items.map((item) => (
            <tr key={item.path}>
              <td className="largest-name" title={item.path}>
                {item.is_dir ? (
                  <button className="largest-link" onClick={() => onDrillDown(item.path)}>
                    {relativePath(item.path, scanRoot)}/
                  </button>
                ) : (
                  relativePath(item.path, scanRoot)
                )}
              </td>
              <td className="largest-size">{formatBytes(item.size)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function LargestList({ scanRoot, files, dirs, onDrillDown }: LargestListProps) {
  if (files.length === 0 && dirs.length === 0) return null

  return (
    <div className="largest">
      <ItemTable title="Largest files" items={files} scanRoot={scanRoot} onDrillDown={onDrillDown} />
      <ItemTable title="Largest directories" items={dirs} scanRoot={scanRoot} onDrillDown={onDrillDown} />
    </div>
  )
}
