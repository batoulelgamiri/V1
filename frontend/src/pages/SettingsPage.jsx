import { Bot, Database, FileArchive, Gauge, KeyRound, ScanSearch, SlidersHorizontal } from 'lucide-react'
import { PageHeader } from '../components/ui/PageHeader'
import { ErrorState, LoadingState } from '../components/ui/States'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useApi } from '../hooks/useApi'

function SettingCard({ icon: Icon, label, value, description }) {
  return <article className="panel p-5"><div className="flex items-start gap-3"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-line bg-elevated text-accent"><Icon className="h-4 w-4" /></div><div><p className="text-xs text-muted">{label}</p><div className="mt-1 text-sm font-medium text-ink">{value}</div><p className="mt-2 text-xs leading-5 text-muted">{description}</p></div></div></article>
}

export function SettingsPage() {
  const { data, loading, error } = useApi('/settings/public')
  if (loading) return <LoadingState />
  if (error) return <ErrorState error={error} />
  return (
    <>
      <PageHeader eyebrow="Operational configuration" title="Settings" description="Read-only, non-sensitive runtime values. Secrets remain on the server and are never exposed here." />
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <SettingCard icon={FileArchive} label="Maximum file size" value={`${data.max_file_size_mb} MB`} description="Enforced while streaming both manual and Wazuh uploads." />
        <SettingCard icon={Gauge} label="Suspicious threshold" value={`${(data.thresholds.suspicious * 100).toFixed(0)}%`} description="Scores at or above this level are suspicious unless they cross the malicious threshold." />
        <SettingCard icon={SlidersHorizontal} label="Malicious threshold" value={`${(data.thresholds.malicious * 100).toFixed(0)}%`} description="Scores at or above this level receive a malicious verdict." />
        <SettingCard icon={Database} label="Detection model" value={data.model_name} description="The verified model artifact and EMBER v2 feature contract are checked before inference." />
        <SettingCard icon={ScanSearch} label="YARA rules" value={<StatusBadge value={data.yara_available ? 'completed' : 'failed'} />} description={`${data.yara_enabled ? 'Enabled' : 'Disabled'} · ${data.yara_ruleset_version}. Rules supply explicit signature evidence alongside XGBoost.`} />
        <SettingCard icon={Bot} label="Report model" value={data.ollama_model} description="Used locally for suspicious and malicious report enrichment only." />
        <SettingCard icon={KeyRound} label="Wazuh authentication" value={<StatusBadge value="completed" />} description="Ingest uses a server-side API key. The key value is intentionally hidden." />
      </section>
      <section className="panel mt-6 p-6"><div className="flex items-center justify-between gap-4"><div><h2 className="text-sm font-medium text-ink">Model artifact</h2><p className="mt-2 text-xs leading-5 text-muted">The backend will not silently substitute incompatible features when the model or exact extractor is missing.</p></div><StatusBadge value={data.model_path_configured ? 'completed' : 'failed'} /></div></section>
    </>
  )
}
