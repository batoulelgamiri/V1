import { ArrowUpRight, FileSearch } from 'lucide-react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../ui/States'
import { StatusBadge } from '../ui/StatusBadge'
import { formatBytes, formatDate, formatScore, truncateHash } from '../../utils/format'

export function AnalysisTable({ items = [], showEndpoint = false }) {
  if (!items.length) return <EmptyState />

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-surface/80 shadow-panel backdrop-blur-sm">
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[780px] text-left">
          <thead className="border-b border-line bg-elevated/50 font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
            <tr>
              <th className="px-5 py-4 font-medium">File / hash</th>
              {showEndpoint && <th className="px-5 py-4 font-medium">Endpoint</th>}
              <th className="px-5 py-4 font-medium">Source</th>
              <th className="px-5 py-4 font-medium">Classification</th>
              <th className="px-5 py-4 font-medium">Score</th>
              <th className="px-5 py-4 font-medium">Observed</th>
              <th className="px-5 py-4" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line/70">
            {items.map((item) => (
              <tr key={item.id} className="transition-colors hover:bg-elevated/35">
                <td className="px-5 py-4">
                  <p className="max-w-[260px] truncate text-sm font-medium text-ink">{item.original_filename}</p>
                  <p className="mt-1 font-mono text-[10px] tracking-wide text-muted">{truncateHash(item.sha256)} · {formatBytes(item.file_size)}</p>
                </td>
                {showEndpoint && <td className="px-5 py-4 text-xs text-muted"><span className="block text-ink">{item.endpoint_name || '—'}</span>{item.endpoint_id || ''}</td>}
                <td className="px-5 py-4 font-mono text-[11px] uppercase tracking-wider text-muted">{item.source}</td>
                <td className="px-5 py-4"><StatusBadge value={item.classification || item.status} /></td>
                <td className="px-5 py-4 font-mono text-sm text-ink">{formatScore(item.score)}</td>
                <td className="px-5 py-4 text-xs text-muted">{formatDate(item.created_at)}</td>
                <td className="px-5 py-4 text-right"><Link className="icon-button inline-flex" to={`/analyses/${item.id}`} aria-label={`Open analysis ${item.id}`}><ArrowUpRight className="h-4 w-4" /></Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="divide-y divide-line md:hidden">
        {items.map((item) => (
          <Link key={item.id} to={`/analyses/${item.id}`} className="block p-4 transition-colors hover:bg-elevated/40">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-lg border border-line bg-elevated p-2 text-accent"><FileSearch className="h-4 w-4" /></div>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2"><p className="truncate text-sm font-medium">{item.original_filename}</p><StatusBadge value={item.classification || item.status} /></div>
                <p className="mt-2 truncate font-mono text-[10px] text-muted">{item.sha256}</p>
                <div className="mt-3 flex items-center justify-between text-xs text-muted"><span>{item.endpoint_name || item.source}</span><span>{formatScore(item.score)}</span></div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

