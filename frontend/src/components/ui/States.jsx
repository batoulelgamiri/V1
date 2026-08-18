import { AlertTriangle, Inbox, LoaderCircle } from 'lucide-react'

export function LoadingState({ label = 'Reading intelligence…' }) {
  return (
    <div className="panel flex min-h-48 items-center justify-center gap-3 text-sm text-muted">
      <LoaderCircle className="h-5 w-5 animate-spin text-accent" /> {label}
    </div>
  )
}

export function ErrorState({ error }) {
  return (
    <div className="panel flex min-h-48 flex-col items-center justify-center gap-3 p-8 text-center">
      <AlertTriangle className="h-6 w-6 text-danger" />
      <p className="text-sm text-muted">{error?.message || 'Unable to load this view.'}</p>
    </div>
  )
}

export function EmptyState({ title = 'No analyses yet', description = 'New results will appear here.' }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 p-8 text-center">
      <Inbox className="h-6 w-6 text-muted" />
      <div>
        <p className="font-medium text-ink">{title}</p>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>
    </div>
  )
}

