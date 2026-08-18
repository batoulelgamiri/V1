const styles = {
  benign: 'border-success/25 bg-success/10 text-success',
  suspicious: 'border-warning/25 bg-warning/10 text-warning',
  malicious: 'border-danger/25 bg-danger/10 text-danger',
  completed: 'border-success/25 bg-success/10 text-success',
  processing: 'border-accent/25 bg-accent/10 text-accent',
  failed: 'border-danger/25 bg-danger/10 text-danger',
}

export function StatusBadge({ value = 'unknown' }) {
  const normalized = String(value || 'unknown').toLowerCase()
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.13em] ${styles[normalized] || 'border-line bg-elevated text-muted'}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {normalized}
    </span>
  )
}

