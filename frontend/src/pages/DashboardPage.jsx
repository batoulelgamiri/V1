import { Activity, AlertTriangle, CheckCircle2, Radar, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { AnalysisTable } from '../components/analysis/AnalysisTable'
import { ActivityBars } from '../components/dashboard/ActivityBars'
import { PageHeader } from '../components/ui/PageHeader'
import { ErrorState, LoadingState } from '../components/ui/States'
import { useApi } from '../hooks/useApi'

const metrics = [
  { key: 'total', label: 'Total analyses', icon: Activity, tone: 'text-accent', line: 'from-accent' },
  { key: 'benign', label: 'Benign', icon: CheckCircle2, tone: 'text-success', line: 'from-success' },
  { key: 'suspicious', label: 'Suspicious', icon: AlertTriangle, tone: 'text-warning', line: 'from-warning' },
  { key: 'malicious', label: 'Malicious', icon: ShieldAlert, tone: 'text-danger', line: 'from-danger' },
]

export function DashboardPage() {
  const { data, loading, error } = useApi('/dashboard/summary')

  if (loading) return <LoadingState label="Assembling the intelligence picture…" />
  if (error) return <ErrorState error={error} />

  return (
    <>
      <PageHeader
        eyebrow="Operational picture"
        title="Security overview"
        description="Static PE verdicts, incoming endpoint detections, and recent analyst activity in one focused view."
        action={<Link className="primary-button" to="/analyze"><Radar className="h-4 w-4" /> Analyze a file</Link>}
      />
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Analysis metrics">
        {metrics.map(({ key, label, icon: Icon, tone, line }) => (
          <article key={key} className="panel group relative overflow-hidden p-5">
            <div className={`absolute inset-x-0 top-0 h-px bg-gradient-to-r ${line} to-transparent opacity-70`} />
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">{label}</span>
              <Icon className={`h-4 w-4 ${tone}`} />
            </div>
            <p className="mt-5 font-mono text-3xl font-semibold tracking-tight text-ink">{data?.[key] ?? 0}</p>
            <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.15em] text-muted">All recorded events</p>
          </article>
        ))}
      </section>
      <section className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_1fr]">
        <article className="panel p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between"><div><p className="text-sm font-medium text-ink">Analysis activity</p><p className="mt-1 text-xs text-muted">Seven-day intake volume</p></div><span className="font-mono text-[10px] uppercase tracking-wider text-muted">Live history</span></div>
          <ActivityBars activity={data?.activity} />
        </article>
        <article className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-6"><div><p className="text-sm font-medium text-ink">Priority detections</p><p className="mt-1 text-xs text-muted">Suspicious and malicious verdicts</p></div><Link to="/history?classification=malicious" className="text-xs font-medium text-accent hover:underline">View history</Link></div>
          {data?.recent_threats?.length ? (
            <div className="divide-y divide-line/70">
              {data.recent_threats.slice(0, 5).map((item) => (
                <Link key={item.id} to={`/analyses/${item.id}`} className="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-elevated/40 sm:px-6">
                  <span className={`h-2 w-2 rounded-full ${item.classification === 'malicious' ? 'bg-danger' : 'bg-warning'}`} />
                  <div className="min-w-0 flex-1"><p className="truncate text-sm text-ink">{item.original_filename}</p><p className="mt-1 truncate font-mono text-[10px] uppercase tracking-wide text-muted">{item.endpoint_name || item.source}</p></div>
                  <span className="font-mono text-xs text-muted">{typeof item.score === 'number' ? `${(item.score * 100).toFixed(1)}%` : '—'}</span>
                </Link>
              ))}
            </div>
          ) : <div className="grid min-h-52 place-items-center px-6 text-center text-sm text-muted">No priority detections recorded.</div>}
        </article>
      </section>
      <section className="mt-6">
        <div className="mb-4 flex items-center justify-between"><h2 className="text-base font-medium text-ink">Recent activity</h2><Link to="/history" className="text-xs font-medium text-accent hover:underline">Complete history</Link></div>
        <AnalysisTable items={data?.recent || []} />
      </section>
    </>
  )
}

