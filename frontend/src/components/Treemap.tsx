import { useMemo } from 'react'
import { computeTreemapLayout } from '../lib/treemap'
import { formatBytes } from '../lib/format'
import { CATEGORY_COLORS, dominantCategory } from '../lib/fileCategory'
import type { TreeNode } from '../lib/types'

const WIDTH = 960
const HEIGHT = 540

interface TreemapProps {
  root: TreeNode
  onDrillDown: (path: string) => void
}

export function Treemap({ root, onDrillDown }: TreemapProps) {
  const rects = useMemo(() => computeTreemapLayout(root, WIDTH, HEIGHT), [root])

  return (
    <svg
      width={WIDTH}
      height={HEIGHT}
      role="img"
      aria-label={`Treemap of ${root.name}, colored by file type`}
      className="viz-surface"
    >
      {rects
        .filter((r) => r.path !== root.path)
        .map((r) => {
          const w = r.x1 - r.x0
          const h = r.y1 - r.y0
          if (w <= 0 || h <= 0) return null
          const fill = CATEGORY_COLORS[dominantCategory(r.node)]
          return (
            <g
              key={r.path}
              transform={`translate(${r.x0}, ${r.y0})`}
              onClick={() => r.is_dir && onDrillDown(r.path)}
              style={{ cursor: r.is_dir ? 'pointer' : 'default' }}
            >
              {/* No border: the 2px gap baked into the layout is what
                  separates tiles -- see marks-and-anatomy.md. */}
              <rect width={w} height={h} fill={fill} />
              <title>{`${r.name} — ${formatBytes(r.value)}`}</title>
              {w > 50 && h > 16 && (
                <text x={4} y={14} fontSize={11} fill="#ffffff" pointerEvents="none">
                  {r.name}
                </text>
              )}
            </g>
          )
        })}
    </svg>
  )
}
