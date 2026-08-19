import { hierarchy, treemap as d3Treemap, type HierarchyRectangularNode } from 'd3-hierarchy'
import type { TreeNode } from './types'

export interface LayoutRect {
  path: string
  name: string
  value: number
  is_dir: boolean
  depth: number
  x0: number
  y0: number
  x1: number
  y1: number
  node: TreeNode
}

/**
 * Pure layout transform: fixture tree in, laid-out rects out. No DOM.
 *
 * A directory node with an empty `children` array is treated as a leaf for
 * layout purposes -- that's either a true leaf/file, or a directory whose
 * children were cut off by the backend's `depth` param. Either way its own
 * `size` (already the full recursive aggregate from the scanner) is the
 * value to plot, since d3 would otherwise sum zero for it.
 */
export function computeTreemapLayout(root: TreeNode, width: number, height: number): LayoutRect[] {
  const h = hierarchy<TreeNode>(root, (d) => (d.children.length > 0 ? d.children : undefined))
    .sum((d) => (d.children.length === 0 ? d.size : 0))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))

  // 2px surface gap between tiles (see marks-and-anatomy.md) -- the gap is
  // geometry, not a stroke; no border is drawn around tiles.
  const layout = d3Treemap<TreeNode>().size([width, height]).paddingInner(2)
  const laidOut = layout(h) as HierarchyRectangularNode<TreeNode>

  const rects: LayoutRect[] = []
  laidOut.each((node) => {
    rects.push({
      path: node.data.path,
      name: node.data.name,
      value: node.value ?? 0,
      is_dir: node.data.is_dir,
      depth: node.depth,
      x0: node.x0,
      y0: node.y0,
      x1: node.x1,
      y1: node.y1,
      node: node.data,
    })
  })
  return rects
}
