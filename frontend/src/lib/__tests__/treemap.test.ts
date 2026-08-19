import { describe, expect, it } from 'vitest'
import { computeTreemapLayout } from '../treemap'
import type { TreeNode } from '../types'

function file(path: string, name: string, size: number): TreeNode {
  return { path, name, size, is_dir: false, mtime: 1, last_scanned: 1, error: null, children: [] }
}

function dir(path: string, name: string, size: number, children: TreeNode[]): TreeNode {
  return { path, name, size, is_dir: true, mtime: 1, last_scanned: 1, error: null, children }
}

describe('computeTreemapLayout', () => {
  it('lays out two equal-size files side by side filling the full area', () => {
    const tree = dir('/root', 'root', 200, [file('/root/a', 'a', 100), file('/root/b', 'b', 100)])

    const rects = computeTreemapLayout(tree, 200, 100)

    const root = rects.find((r) => r.path === '/root')!
    expect(root.x0).toBe(0)
    expect(root.y0).toBe(0)
    expect(root.x1).toBe(200)
    expect(root.y1).toBe(100)

    const a = rects.find((r) => r.path === '/root/a')!
    const b = rects.find((r) => r.path === '/root/b')!
    expect(a.value).toBe(100)
    expect(b.value).toBe(100)
    // equal values -> equal areas
    const areaA = (a.x1 - a.x0) * (a.y1 - a.y0)
    const areaB = (b.x1 - b.x0) * (b.y1 - b.y0)
    expect(areaA).toBeCloseTo(areaB, 5)
  })

  it('gives a larger file a proportionally larger area', () => {
    const tree = dir('/root', 'root', 300, [file('/root/big', 'big', 200), file('/root/small', 'small', 100)])

    const rects = computeTreemapLayout(tree, 300, 100)
    const big = rects.find((r) => r.path === '/root/big')!
    const small = rects.find((r) => r.path === '/root/small')!

    const areaBig = (big.x1 - big.x0) * (big.y1 - big.y0)
    const areaSmall = (small.x1 - small.x0) * (small.y1 - small.y0)
    // paddingInner introduces small gaps, so compare the ratio loosely rather than exact area
    expect(areaBig / areaSmall).toBeGreaterThan(1.9)
    expect(areaBig / areaSmall).toBeLessThan(2.1)
  })

  it('treats a depth-truncated directory (size set, children empty) as a leaf value', () => {
    const truncated = dir('/root/deep', 'deep', 500, []) // backend cut off children at depth limit
    const tree = dir('/root', 'root', 500, [truncated])

    const rects = computeTreemapLayout(tree, 100, 100)
    const deep = rects.find((r) => r.path === '/root/deep')!
    expect(deep.value).toBe(500)
  })

  it('does not double count a directory that has children present', () => {
    const tree = dir('/root', 'root', 150, [
      dir('/root/sub', 'sub', 150, [file('/root/sub/f', 'f', 150)]),
    ])

    const rects = computeTreemapLayout(tree, 100, 100)
    const root = rects.find((r) => r.path === '/root')!
    const sub = rects.find((r) => r.path === '/root/sub')!
    expect(root.value).toBe(150)
    expect(sub.value).toBe(150)
  })

  it('produces one rect per node including the root', () => {
    const tree = dir('/root', 'root', 30, [file('/root/a', 'a', 10), file('/root/b', 'b', 20)])
    const rects = computeTreemapLayout(tree, 100, 100)
    expect(rects).toHaveLength(3)
  })
})
