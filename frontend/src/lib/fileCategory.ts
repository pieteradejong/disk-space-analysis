import type { TreeNode } from './types'

export type FileCategory = 'video' | 'photos' | 'documents' | 'audio' | 'archives' | 'apps' | 'other'

// Fixed order = the categorical color order everywhere (treemap fill, breakdown
// bar, legend). Never reorder based on data -- identity must stay stable.
export const CATEGORY_ORDER: FileCategory[] = [
  'video', 'photos', 'documents', 'audio', 'archives', 'apps', 'other',
]

export const CATEGORY_LABELS: Record<FileCategory, string> = {
  video: 'Video',
  photos: 'Photos',
  documents: 'Documents',
  audio: 'Audio',
  archives: 'Archives',
  apps: 'Apps',
  other: 'Other',
}

// Categorical slots 1-6 (blue, orange, aqua, yellow, magenta, green) from the
// validated default palette, dark-mode steps (this app is currently
// dark-only) -- validated as an adjacent-pairlist-safe set via
// scripts/validate_palette.js (worst adjacent CVD ΔE 8.4, normal-vision 19.3,
// both above the 8/15 floors). "Other" is deliberately a neutral gray, not a
// seventh identity hue -- it's a catch-all, not a category someone needs to
// visually track, so it's exempt from the categorical chroma-floor check the
// same way a muted/axis token is.
export const CATEGORY_COLORS: Record<FileCategory, string> = {
  video: '#3987e5',
  photos: '#d95926',
  documents: '#199e70',
  audio: '#c98500',
  archives: '#d55181',
  apps: '#008300',
  other: '#898781',
}

const VIDEO_EXTENSIONS = new Set([
  'mp4', 'mov', 'mkv', 'avi', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg', 'ts', '3gp',
])

const PHOTO_EXTENSIONS = new Set([
  'jpg', 'jpeg', 'png', 'gif', 'heic', 'heif', 'bmp', 'tiff', 'tif', 'webp',
  'raw', 'cr2', 'cr3', 'nef', 'arw', 'dng', 'svg',
])

const DOCUMENT_EXTENSIONS = new Set([
  'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'rtf',
  'pages', 'numbers', 'key', 'csv', 'epub',
])

const AUDIO_EXTENSIONS = new Set([
  'mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma', 'aiff', 'alac',
])

const ARCHIVE_EXTENSIONS = new Set([
  'zip', 'tar', 'gz', 'tgz', 'bz2', 'xz', '7z', 'rar', 'dmg', 'iso',
])

const APP_EXTENSIONS = new Set(['app', 'pkg', 'ipa'])

export function categorizeFile(name: string): FileCategory {
  const dot = name.lastIndexOf('.')
  if (dot <= 0 || dot === name.length - 1) return 'other'
  const ext = name.slice(dot + 1).toLowerCase()
  if (VIDEO_EXTENSIONS.has(ext)) return 'video'
  if (PHOTO_EXTENSIONS.has(ext)) return 'photos'
  if (DOCUMENT_EXTENSIONS.has(ext)) return 'documents'
  if (AUDIO_EXTENSIONS.has(ext)) return 'audio'
  if (ARCHIVE_EXTENSIONS.has(ext)) return 'archives'
  if (APP_EXTENSIONS.has(ext)) return 'apps'
  return 'other'
}

type CategoryTotals = Record<FileCategory, number>

function emptyTotals(): CategoryTotals {
  return { video: 0, photos: 0, documents: 0, audio: 0, archives: 0, apps: 0, other: 0 }
}

/**
 * Recursively sums leaf-file bytes by category under `node`.
 *
 * A directory with no fetched children -- either genuinely empty, or cut off
 * by the backend's `depth` param -- has unknown composition and is bucketed
 * as "other" rather than guessed. Drilling into it fetches its real children
 * and the coloring becomes accurate from that point on.
 */
export function categoryBytes(node: TreeNode): CategoryTotals {
  if (!node.is_dir) {
    const totals = emptyTotals()
    totals[categorizeFile(node.name)] = node.size
    return totals
  }
  if (node.children.length === 0) {
    const totals = emptyTotals()
    totals.other = node.size
    return totals
  }
  const totals = emptyTotals()
  for (const child of node.children) {
    const childTotals = categoryBytes(child)
    for (const category of CATEGORY_ORDER) {
      totals[category] += childTotals[category]
    }
  }
  return totals
}

/** The category a treemap tile should be filled with. */
export function dominantCategory(node: TreeNode): FileCategory {
  if (!node.is_dir) return categorizeFile(node.name)
  const totals = categoryBytes(node)
  let best: FileCategory = 'other'
  for (const category of CATEGORY_ORDER) {
    if (totals[category] > totals[best]) best = category
  }
  return best
}

export interface BreakdownEntry {
  category: FileCategory
  bytes: number
}

/** Byte totals per category for `root`, in fixed CATEGORY_ORDER. */
export function computeBreakdown(root: TreeNode): BreakdownEntry[] {
  const totals = categoryBytes(root)
  return CATEGORY_ORDER.map((category) => ({ category, bytes: totals[category] }))
}
