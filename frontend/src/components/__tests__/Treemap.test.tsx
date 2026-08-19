import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Treemap } from '../Treemap'
import { CATEGORY_COLORS } from '../../lib/fileCategory'
import type { TreeNode } from '../../lib/types'

function file(path: string, name: string, size: number): TreeNode {
  return { path, name, size, is_dir: false, mtime: 1, last_scanned: 1, error: null, children: [] }
}

function dir(path: string, name: string, size: number, children: TreeNode[]): TreeNode {
  return { path, name, size, is_dir: true, mtime: 1, last_scanned: 1, error: null, children }
}

describe('Treemap', () => {
  it('renders one rect per non-root node', () => {
    const tree = dir('/root', 'root', 30, [file('/root/a', 'a', 10), file('/root/b', 'b', 20)])
    const { container } = render(<Treemap root={tree} onDrillDown={() => {}} />)
    expect(container.querySelectorAll('rect')).toHaveLength(2)
  })

  it('shows the name label for large-enough rects', () => {
    const tree = dir('/root', 'root', 30, [file('/root/a', 'a', 30)])
    render(<Treemap root={tree} onDrillDown={() => {}} />)
    expect(screen.getByText('a')).toBeInTheDocument()
  })

  it('calls onDrillDown with the directory path when a directory tile is clicked', () => {
    const tree = dir('/root', 'root', 10, [dir('/root/sub', 'sub', 10, [file('/root/sub/f', 'f', 10)])])
    const onDrillDown = vi.fn()
    const { container } = render(<Treemap root={tree} onDrillDown={onDrillDown} />)

    const subGroup = container.querySelector('g')
    subGroup?.dispatchEvent(new MouseEvent('click', { bubbles: true }))

    expect(onDrillDown).toHaveBeenCalledWith('/root/sub')
  })

  it('does not call onDrillDown when a file tile is clicked', () => {
    const tree = dir('/root', 'root', 10, [file('/root/a', 'a', 10)])
    const onDrillDown = vi.fn()
    const { container } = render(<Treemap root={tree} onDrillDown={onDrillDown} />)

    const group = container.querySelector('g')
    group?.dispatchEvent(new MouseEvent('click', { bubbles: true }))

    expect(onDrillDown).not.toHaveBeenCalled()
  })

  it('fills a video file tile with the video category color', () => {
    const tree = dir('/root', 'root', 10, [file('/root/clip.mp4', 'clip.mp4', 10)])
    const { container } = render(<Treemap root={tree} onDrillDown={() => {}} />)
    expect(container.querySelector('rect')).toHaveAttribute('fill', CATEGORY_COLORS.video)
  })

  it('fills a directory tile by its byte-majority category, independent of its own leaf tiles', () => {
    // the "stash" dir is 90% jpg / 10% txt by bytes -> its own tile should read as photos,
    // even though the txt leaf underneath it still reads as other on its own tile.
    const tree = dir('/root', 'root', 100, [
      dir('/root/stash', 'stash', 100, [file('/root/stash/a.jpg', 'a.jpg', 90), file('/root/stash/b.txt', 'b.txt', 10)]),
    ])
    const { container } = render(<Treemap root={tree} onDrillDown={() => {}} />)
    const groups = container.querySelectorAll('g')
    const stashRect = [...groups].find((g) => g.querySelector('title')?.textContent?.startsWith('stash'))
    expect(stashRect?.querySelector('rect')).toHaveAttribute('fill', CATEGORY_COLORS.photos)
  })

  it('does not draw a border stroke around tiles (the gap does the separating)', () => {
    const tree = dir('/root', 'root', 10, [file('/root/a', 'a', 10)])
    const { container } = render(<Treemap root={tree} onDrillDown={() => {}} />)
    expect(container.querySelector('rect')).not.toHaveAttribute('stroke')
  })
})
