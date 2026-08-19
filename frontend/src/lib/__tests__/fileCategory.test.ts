import { describe, expect, it } from 'vitest'
import { categorizeFile, categoryBytes, computeBreakdown, dominantCategory } from '../fileCategory'
import type { TreeNode } from '../types'

function file(path: string, name: string, size: number): TreeNode {
  return { path, name, size, is_dir: false, mtime: 1, last_scanned: 1, error: null, children: [] }
}

function dir(path: string, name: string, size: number, children: TreeNode[]): TreeNode {
  return { path, name, size, is_dir: true, mtime: 1, last_scanned: 1, error: null, children }
}

describe('categorizeFile', () => {
  it('recognizes video extensions case-insensitively', () => {
    expect(categorizeFile('movie.MP4')).toBe('video')
    expect(categorizeFile('clip.mov')).toBe('video')
  })

  it('recognizes photo extensions', () => {
    expect(categorizeFile('pic.jpg')).toBe('photos')
    expect(categorizeFile('scan.HEIC')).toBe('photos')
  })

  it('recognizes document, audio, archive, and app extensions', () => {
    expect(categorizeFile('report.pdf')).toBe('documents')
    expect(categorizeFile('song.MP3')).toBe('audio')
    expect(categorizeFile('backup.zip')).toBe('archives')
    expect(categorizeFile('archive.tar.gz')).toBe('archives') // last extension (.gz) wins
    expect(categorizeFile('Installer.pkg')).toBe('apps')
  })

  it('falls back to other for unknown or missing extensions', () => {
    expect(categorizeFile('README')).toBe('other')
    expect(categorizeFile('notes')).toBe('other')
  })

  it('treats a leading dot (dotfile) as no extension, not other-mislabeled', () => {
    expect(categorizeFile('.gitignore')).toBe('other')
  })
})

describe('categoryBytes / computeBreakdown', () => {
  it('sums leaf bytes by category across a nested tree', () => {
    const tree = dir('/root', 'root', 300, [
      file('/root/a.mp4', 'a.mp4', 100),
      dir('/root/sub', 'sub', 200, [file('/root/sub/b.jpg', 'b.jpg', 150), file('/root/sub/c.bin', 'c.bin', 50)]),
    ])

    const totals = categoryBytes(tree)
    expect(totals).toEqual({
      video: 100, photos: 150, documents: 0, audio: 0, archives: 0, apps: 0, other: 50,
    })

    const breakdown = computeBreakdown(tree)
    expect(breakdown).toEqual([
      { category: 'video', bytes: 100 },
      { category: 'photos', bytes: 150 },
      { category: 'documents', bytes: 0 },
      { category: 'audio', bytes: 0 },
      { category: 'archives', bytes: 0 },
      { category: 'apps', bytes: 0 },
      { category: 'other', bytes: 50 },
    ])
  })

  it('buckets a depth-truncated directory (size set, no children) as other', () => {
    const truncated = dir('/root/deep', 'deep', 500, [])
    const tree = dir('/root', 'root', 500, [truncated])

    expect(categoryBytes(tree)).toEqual({
      video: 0, photos: 0, documents: 0, audio: 0, archives: 0, apps: 0, other: 500,
    })
  })
})

describe('dominantCategory', () => {
  it('returns a file leaf category directly', () => {
    expect(dominantCategory(file('/a.mp4', 'a.mp4', 10))).toBe('video')
  })

  it('returns the byte-majority category for a directory', () => {
    const tree = dir('/root', 'root', 100, [file('/root/a.mp4', 'a.mp4', 90), file('/root/b.jpg', 'b.jpg', 10)])
    expect(dominantCategory(tree)).toBe('video')
  })

  it('defaults an empty directory to other rather than picking video by tie', () => {
    expect(dominantCategory(dir('/root/empty', 'empty', 0, []))).toBe('other')
  })
})
