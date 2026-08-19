interface BreadcrumbProps {
  scanRoot: string
  currentPath: string
  onNavigate: (path: string) => void
}

export function Breadcrumb({ scanRoot, currentPath, onNavigate }: BreadcrumbProps) {
  const relative = currentPath.startsWith(scanRoot) ? currentPath.slice(scanRoot.length) : currentPath
  const segments = relative.split('/').filter(Boolean)

  const crumbs: { label: string; path: string }[] = [{ label: scanRoot, path: scanRoot }]
  let acc = scanRoot
  for (const seg of segments) {
    acc = `${acc}/${seg}`
    crumbs.push({ label: seg, path: acc })
  }

  return (
    <nav aria-label="breadcrumb">
      {crumbs.map((c, i) => (
        <span key={c.path}>
          {i > 0 && ' / '}
          <button
            onClick={() => onNavigate(c.path)}
            disabled={c.path === currentPath}
            style={{ fontWeight: c.path === currentPath ? 'bold' : 'normal' }}
          >
            {c.label}
          </button>
        </span>
      ))}
    </nav>
  )
}
