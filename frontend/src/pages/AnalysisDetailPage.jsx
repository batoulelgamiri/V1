import { ArrowLeft, Box, BrainCircuit, Download, FileCode2, Fingerprint, ShieldAlert } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { PageHeader } from '../components/ui/PageHeader'
import { ErrorState, LoadingState } from '../components/ui/States'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useApi } from '../hooks/useApi'
import { pdfUrl } from '../services/api'
import { formatBytes, formatDate, formatScore } from '../utils/format'

function InfoRow({ label, children, mono = false }) {
  return <div className="grid gap-1 border-b border-line/65 py-3 last:border-0 sm:grid-cols-[155px_1fr]"><dt className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{label}</dt><dd className={`min-w-0 break-words text-sm text-ink ${mono ? 'font-mono text-xs' : ''}`}>{children || '—'}</dd></div>
}

function ReportPanel({ analysis, reportData, reportLoading }) {
  if (!analysis.classification || analysis.classification === 'benign') return null
  if (reportLoading) return <LoadingState label="Reading structured report…" />
  if (!reportData) {
    return (
      <section className="panel p-6">
        <div className="flex items-start gap-3"><BrainCircuit className="mt-0.5 h-5 w-5 text-warning" /><div><h2 className="font-medium text-ink">AI analysis unavailable</h2><p className="mt-2 text-sm leading-6 text-muted">The core classifier result remains valid and stored. Ollama may be offline or the report response did not pass schema validation.</p></div></div>
      </section>
    )
  }
  if (!reportData.report) {
    return <section className="panel p-6"><h2 className="font-medium text-ink">AI analysis unavailable</h2><p className="mt-2 text-sm leading-6 text-muted">{reportData.error_message || 'Structured report generation did not complete.'}</p></section>
  }
  const report = reportData.report
  return (
    <section className="panel overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-line p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl border border-accent/25 bg-accent/10 text-accent"><BrainCircuit className="h-5 w-5" /></div><div><h2 className="font-medium text-ink">AI analysis report</h2><p className="mt-1 text-xs text-muted">Validated structured output · {report.risk_level} risk</p></div></div>
        {reportData.pdf_available && <a href={pdfUrl(analysis.id)} className="secondary-button"><Download className="h-4 w-4" /> Download PDF</a>}
      </div>
      <div className="p-5 sm:p-6">
        <p className="text-sm leading-7 text-muted">{report.executive_summary}</p>
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div>
            <div className="mb-3 flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-success" /><h3 className="text-sm font-medium text-ink">Confirmed Evidence</h3></div>
            <div className="space-y-3">{report.confirmed_indicators.length ? report.confirmed_indicators.map((item, index) => <div key={`${item.indicator}-${index}`} className="rounded-xl border border-success/15 bg-success/5 p-4"><p className="text-sm font-medium text-ink">{item.indicator}</p><p className="mt-2 text-xs leading-5 text-muted">{item.evidence}</p></div>) : <p className="text-sm text-muted">No confirmed indicators were listed.</p>}</div>
          </div>
          <div>
            <div className="mb-3 flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-warning" /><h3 className="text-sm font-medium text-ink">Suspected Behavior</h3></div>
            <div className="space-y-3">{report.suspected_capabilities.length ? report.suspected_capabilities.map((item, index) => <div key={`${item.capability}-${index}`} className="rounded-xl border border-warning/15 bg-warning/5 p-4"><div className="flex items-start justify-between gap-2"><p className="text-sm font-medium text-ink">{item.capability}</p><span className="font-mono text-[9px] uppercase tracking-wider text-warning">{item.confidence}</span></div><p className="mt-2 text-xs leading-5 text-muted">{item.evidence.join(' · ')}</p></div>) : <p className="text-sm text-muted">No supported capabilities were inferred.</p>}</div>
          </div>
        </div>
        {report.mitre_attack.length > 0 && <div className="mt-8"><h3 className="text-sm font-medium text-ink">Possible MITRE ATT&CK mappings</h3><div className="mt-3 grid gap-3 md:grid-cols-2">{report.mitre_attack.map((item) => <div key={item.technique_id} className="rounded-xl border border-line bg-canvas/45 p-4"><div className="flex gap-2"><span className="font-mono text-xs text-accent">{item.technique_id}</span><span className="text-sm text-ink">{item.technique_name}</span></div><p className="mt-2 text-xs leading-5 text-muted">{item.evidence}</p></div>)}</div></div>}
        <div className="mt-8 grid gap-6 lg:grid-cols-2"><div><h3 className="text-sm font-medium text-ink">Analyst recommendations</h3><ul className="mt-3 space-y-2 text-sm leading-6 text-muted">{report.recommendations.map((item, index) => <li key={index} className="flex gap-2"><span className="text-accent">—</span>{item}</li>)}</ul></div><div><h3 className="text-sm font-medium text-ink">Limitations</h3><ul className="mt-3 space-y-2 text-sm leading-6 text-muted">{report.limitations.map((item, index) => <li key={index} className="flex gap-2"><span className="text-muted">—</span>{item}</li>)}</ul></div></div>
      </div>
    </section>
  )
}

export function AnalysisDetailPage() {
  const { analysisId } = useParams()
  const { data: analysis, loading, error } = useApi(`/analyses/${analysisId}`)
  const reportPath = analysis?.report_available ? `/analyses/${analysisId}/report` : null
  const { data: report, loading: reportLoading } = useApi(reportPath, [analysis?.report_available])

  if (loading) return <LoadingState label="Loading technical evidence…" />
  if (error) return <ErrorState error={error} />
  const technical = analysis?.technical_data || {}

  return (
    <>
      <Link to="/history" className="mb-5 inline-flex items-center gap-2 text-xs text-muted transition-colors hover:text-accent"><ArrowLeft className="h-3.5 w-3.5" /> Back to history</Link>
      <PageHeader
        eyebrow={`Analysis #${analysis.id}`}
        title={analysis.original_filename}
        description={`Observed ${formatDate(analysis.created_at)} · ${analysis.source} intake${analysis.cached_from_analysis_id ? ` · cached from #${analysis.cached_from_analysis_id}` : ''}`}
        action={<StatusBadge value={analysis.classification || analysis.status} />}
      />
      {analysis.error_message && <div className="mb-6 flex items-start gap-3 rounded-xl border border-warning/25 bg-warning/10 p-4 text-sm text-warning"><ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" /><div><p className="font-medium">Analysis incomplete</p><p className="mt-1 leading-5">{analysis.error_message}</p></div></div>}
      <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="panel p-5"><p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Classification</p><div className="mt-4"><StatusBadge value={analysis.classification || analysis.status} /></div></article>
        <article className="panel p-5"><p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Detection score</p><p className="mt-3 font-mono text-2xl font-semibold text-ink">{formatScore(analysis.score)}</p></article>
        <article className="panel p-5"><p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Architecture</p><p className="mt-3 text-lg font-medium text-ink">{technical.architecture || '—'}</p></article>
        <article className="panel p-5"><p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Overall entropy</p><p className="mt-3 font-mono text-2xl font-semibold text-ink">{technical.overall_entropy ?? '—'}</p></article>
      </section>
      <div className="mb-6 grid gap-6 xl:grid-cols-2">
        <section className="panel p-5 sm:p-6"><div className="mb-4 flex items-center gap-2"><FileCode2 className="h-4 w-4 text-accent" /><h2 className="text-sm font-medium text-ink">File Information</h2></div><dl><InfoRow label="File size">{formatBytes(analysis.file_size)}</InfoRow><InfoRow label="File type">{analysis.file_type}</InfoRow><InfoRow label="SHA-256" mono>{analysis.sha256}</InfoRow><InfoRow label="Source">{analysis.source}</InfoRow><InfoRow label="Endpoint">{analysis.endpoint_name ? `${analysis.endpoint_name} (${analysis.endpoint_id})` : '—'}</InfoRow><InfoRow label="Endpoint path" mono>{analysis.file_path}</InfoRow></dl></section>
        <section className="panel p-5 sm:p-6"><div className="mb-4 flex items-center gap-2"><Fingerprint className="h-4 w-4 text-accent" /><h2 className="text-sm font-medium text-ink">PE Metadata</h2></div><dl><InfoRow label="Compiled">{technical.compiled_at ? formatDate(technical.compiled_at) : '—'}</InfoRow><InfoRow label="Entry point" mono>{technical.entry_point}</InfoRow><InfoRow label="Image base" mono>{technical.image_base}</InfoRow><InfoRow label="Subsystem">{technical.subsystem}</InfoRow><InfoRow label="Characteristics" mono>{technical.characteristics}</InfoRow><InfoRow label="Model version" mono>{analysis.model_version}</InfoRow></dl></section>
      </div>
      {technical.sections?.length > 0 && <section className="panel mb-6 overflow-hidden"><div className="flex items-center gap-2 border-b border-line p-5 sm:p-6"><Box className="h-4 w-4 text-accent" /><h2 className="text-sm font-medium text-ink">Technical Indicators · Sections</h2></div><div className="overflow-x-auto"><table className="w-full min-w-[620px] text-left text-xs"><thead className="bg-elevated/45 font-mono text-[9px] uppercase tracking-[0.14em] text-muted"><tr><th className="px-5 py-3">Name</th><th className="px-5 py-3">Virtual size</th><th className="px-5 py-3">Raw size</th><th className="px-5 py-3">Entropy</th><th className="px-5 py-3">Characteristics</th></tr></thead><tbody className="divide-y divide-line">{technical.sections.map((section, index) => <tr key={`${section.name}-${index}`}><td className="px-5 py-3 font-mono text-accent">{section.name}</td><td className="px-5 py-3 text-muted">{formatBytes(section.virtual_size)}</td><td className="px-5 py-3 text-muted">{formatBytes(section.raw_size)}</td><td className="px-5 py-3 font-mono text-ink">{section.entropy}</td><td className="px-5 py-3 font-mono text-muted">{section.characteristics}</td></tr>)}</tbody></table></div></section>}
      {technical.imports?.length > 0 && <section className="panel mb-6 p-5 sm:p-6"><h2 className="text-sm font-medium text-ink">Imported libraries and symbols</h2><p className="mt-2 text-xs text-muted">Static imports are confirmed file structure; they do not prove runtime use.</p><div className="mt-5 grid gap-3 lg:grid-cols-2">{technical.imports.map((entry, index) => <details key={`${entry.library}-${index}`} className="rounded-xl border border-line bg-canvas/40 p-4"><summary className="cursor-pointer font-mono text-xs text-accent">{entry.library} <span className="ml-1 text-muted">({entry.symbols.length})</span></summary><div className="mt-3 flex flex-wrap gap-1.5">{entry.symbols.map((symbol, itemIndex) => <span key={`${symbol}-${itemIndex}`} className="rounded-md bg-elevated px-2 py-1 font-mono text-[9px] text-muted">{symbol}</span>)}</div></details>)}</div></section>}
      <ReportPanel analysis={analysis} reportData={report} reportLoading={reportLoading} />
    </>
  )
}

