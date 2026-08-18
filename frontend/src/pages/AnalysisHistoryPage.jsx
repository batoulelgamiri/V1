import { useMemo, useState } from 'react'
import { Filter, Search } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { AnalysisTable } from '../components/analysis/AnalysisTable'
import { PageHeader } from '../components/ui/PageHeader'
import { ErrorState, LoadingState } from '../components/ui/States'
import { useApi } from '../hooks/useApi'

export function AnalysisHistoryPage() {
  const [params] = useSearchParams()
  const [search, setSearch] = useState('')
  const [classification, setClassification] = useState(params.get('classification') || '')
  const [source, setSource] = useState('')
  const [page, setPage] = useState(1)
  const query = useMemo(() => {
    const values = new URLSearchParams({ page: String(page), page_size: '20' })
    if (search.trim()) values.set('search', search.trim())
    if (classification) values.set('classification', classification)
    if (source) values.set('source', source)
    return `/analyses?${values}`
  }, [page, search, classification, source])
  const { data, loading, error } = useApi(query)

  return (
    <>
      <PageHeader eyebrow="Evidence archive" title="Analysis history" description="Search every manual and endpoint-originated static analysis event." />
      <div className="mb-5 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <label className="input-shell"><Search className="h-4 w-4 text-muted" /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search file, hash, endpoint, or path" /></label>
        <label className="select-shell"><Filter className="h-4 w-4 text-muted" /><select value={classification} onChange={(event) => { setClassification(event.target.value); setPage(1) }}><option value="">All classifications</option><option value="benign">Benign</option><option value="suspicious">Suspicious</option><option value="malicious">Malicious</option></select></label>
        <label className="select-shell"><select value={source} onChange={(event) => { setSource(event.target.value); setPage(1) }}><option value="">All sources</option><option value="manual">Manual</option><option value="wazuh">Wazuh</option></select></label>
      </div>
      {loading ? <LoadingState /> : error ? <ErrorState error={error} /> : <AnalysisTable items={data?.items || []} showEndpoint />}
      {data && data.pages > 1 && <div className="mt-5 flex items-center justify-between"><p className="font-mono text-[11px] text-muted">Page {data.page} of {data.pages} · {data.total} records</p><div className="flex gap-2"><button className="secondary-button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</button><button className="secondary-button" disabled={page >= data.pages} onClick={() => setPage((value) => value + 1)}>Next</button></div></div>}
    </>
  )
}

