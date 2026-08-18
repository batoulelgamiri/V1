import { useMemo, useState } from 'react'
import { RadioTower, Search } from 'lucide-react'
import { AnalysisTable } from '../components/analysis/AnalysisTable'
import { PageHeader } from '../components/ui/PageHeader'
import { ErrorState, LoadingState } from '../components/ui/States'
import { useApi } from '../hooks/useApi'

export function WazuhDetectionsPage() {
  const [search, setSearch] = useState('')
  const [classification, setClassification] = useState('')
  const path = useMemo(() => {
    const query = new URLSearchParams({ source: 'wazuh', page_size: '50' })
    if (search.trim()) query.set('search', search.trim())
    if (classification) query.set('classification', classification)
    return `/analyses?${query}`
  }, [search, classification])
  const { data, loading, error } = useApi(path)

  return (
    <>
      <PageHeader
        eyebrow="Endpoint telemetry"
        title="Wazuh detections"
        description="Files securely forwarded by endpoint-side integrations. Wazuh configuration remains external to this dashboard."
        action={<div className="inline-flex items-center gap-2 rounded-full border border-success/20 bg-success/10 px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-success"><RadioTower className="h-3.5 w-3.5" /> Intake monitored</div>}
      />
      <div className="mb-5 grid gap-3 sm:grid-cols-[1fr_auto]">
        <label className="input-shell"><Search className="h-4 w-4 text-muted" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter endpoint, file, hash, or path" /></label>
        <label className="select-shell"><select value={classification} onChange={(event) => setClassification(event.target.value)}><option value="">All verdicts</option><option value="benign">Benign</option><option value="suspicious">Suspicious</option><option value="malicious">Malicious</option></select></label>
      </div>
      {loading ? <LoadingState label="Reading endpoint detections…" /> : error ? <ErrorState error={error} /> : <AnalysisTable items={data?.items || []} showEndpoint />}
    </>
  )
}

