import { CATEGORY_COLORS, CATEGORY_LABELS, computeBreakdown } from '../lib/fileCategory'
import { formatBytes } from '../lib/format'
import type { TreeNode } from '../lib/types'

const BAR_WIDTH = 960
const BAR_HEIGHT = 20
const GAP = 2
// Below this, an inline label wouldn't fit with padding -- it goes to the
// legend/tooltip instead rather than being clipped.
const MIN_LABEL_WIDTH = 60

interface Segment {
  category: keyof typeof CATEGORY_COLORS
  bytes: number
  x: number
  width: number
  pct: number
}

function layoutSegments(root: TreeNode): Segment[] {
  const entries = computeBreakdown(root).filter((e) => e.bytes > 0)
  const total = entries.reduce((sum, e) => sum + e.bytes, 0)
  if (total === 0) return []

  let x = 0
  return entries.map((e, i) => {
    const rawWidth = (e.bytes / total) * BAR_WIDTH
    const isLast = i === entries.length - 1
    const width = Math.max(rawWidth - (isLast ? 0 : GAP), 0)
    const seg: Segment = { category: e.category, bytes: e.bytes, x, width, pct: (e.bytes / total) * 100 }
    x += rawWidth
    return seg
  })
}

interface BreakdownBarProps {
  root: TreeNode
}

export function BreakdownBar({ root }: BreakdownBarProps) {
  const segments = layoutSegments(root)
  if (segments.length === 0) return null

  return (
    <div className="breakdown">
      <svg
        width={BAR_WIDTH}
        height={BAR_HEIGHT}
        viewBox={`0 0 ${BAR_WIDTH} ${BAR_HEIGHT}`}
        style={{ width: '100%', height: BAR_HEIGHT, maxWidth: BAR_WIDTH }}
        role="img"
        aria-label="Storage breakdown by file type"
        className="viz-surface"
      >
        {segments.map((s) => (
          <g key={s.category}>
            <rect x={s.x} y={0} width={s.width} height={BAR_HEIGHT} fill={CATEGORY_COLORS[s.category]}>
              <title>{`${CATEGORY_LABELS[s.category]} — ${formatBytes(s.bytes)} (${s.pct.toFixed(1)}%)`}</title>
            </rect>
            {s.width >= MIN_LABEL_WIDTH && (
              <text x={s.x + 6} y={BAR_HEIGHT / 2 + 4} fontSize={11} fill="#ffffff" pointerEvents="none">
                {CATEGORY_LABELS[s.category]}
              </text>
            )}
          </g>
        ))}
      </svg>

      <ul className="breakdown-legend">
        {segments.map((s) => (
          <li key={s.category}>
            <span className="swatch" style={{ background: CATEGORY_COLORS[s.category] }} aria-hidden="true" />
            {CATEGORY_LABELS[s.category]} — {formatBytes(s.bytes)}
          </li>
        ))}
      </ul>
    </div>
  )
}
