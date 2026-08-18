export function formatBytes(value = 0) {
  if (!Number.isFinite(value)) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = value
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${size >= 10 || unit === 0 ? size.toFixed(0) : size.toFixed(1)} ${units[unit]}`
}

export function formatScore(score) {
  return typeof score === 'number' ? `${(score * 100).toFixed(1)}%` : '—'
}

export function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function truncateHash(value = '', length = 14) {
  return value.length > length ? `${value.slice(0, length)}…` : value
}

