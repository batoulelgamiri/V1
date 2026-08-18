import { useRef, useState } from 'react'
import { CheckCircle2, File, FileWarning, ScanLine, UploadCloud, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useApi } from '../hooks/useApi'
import { uploadAnalysis } from '../services/api'
import { formatBytes, formatScore } from '../utils/format'

export function ManualAnalysisPage() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [phase, setPhase] = useState('idle')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const { data: settings } = useApi('/settings/public')

  const chooseFile = (candidate) => {
    setError('')
    setResult(null)
    if (!candidate) return
    const maxBytes = (settings?.max_file_size_mb || 100) * 1024 * 1024
    if (candidate.size > maxBytes) {
      setFile(null)
      setError(`File exceeds the configured ${settings?.max_file_size_mb || 100} MB limit.`)
      return
    }
    if (!candidate.size) {
      setFile(null)
      setError('The selected file is empty.')
      return
    }
    setFile(candidate)
    setPhase('ready')
  }

  const submit = async () => {
    if (!file) return
    setError('')
    setResult(null)
    setProgress(0)
    setPhase('uploading')
    try {
      const response = await uploadAnalysis(file, (value) => {
        setProgress(value)
        if (value >= 100) setPhase('analyzing')
      })
      setResult(response)
      setPhase('complete')
    } catch (requestError) {
      setError(requestError.message)
      setPhase('ready')
    }
  }

  const reset = () => {
    setFile(null)
    setResult(null)
    setError('')
    setProgress(0)
    setPhase('idle')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <>
      <PageHeader eyebrow="Manual intake" title="Analyze a PE file" description="Submit one Windows Portable Executable for controlled static inspection. The file is never executed." />
      <div className="grid gap-6 xl:grid-cols-[1.2fr_.8fr]">
        <section className="panel overflow-hidden p-4 sm:p-6">
          <div
            className={`drop-zone relative grid min-h-[390px] place-items-center overflow-hidden rounded-2xl border border-dashed p-6 text-center transition-all ${dragging ? 'border-accent bg-accent/10 shadow-glow' : 'border-line bg-canvas/35 hover:border-accent/50'}`}
            onDragEnter={(event) => { event.preventDefault(); setDragging(true) }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false) }}
            onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]) }}
          >
            <div className="pointer-events-none absolute inset-0 opacity-30 [background:radial-gradient(circle_at_center,rgb(var(--color-accent)/.14),transparent_58%)]" />
            <div className="relative max-w-md">
              <div className={`mx-auto grid h-16 w-16 place-items-center rounded-2xl border transition-all ${dragging ? 'scale-105 border-accent/50 bg-accent/15 text-accent shadow-glow' : 'border-line bg-elevated text-muted'}`}>
                {file ? <File className="h-7 w-7" /> : <UploadCloud className="h-7 w-7" />}
              </div>
              {file ? (
                <div className="mt-6">
                  <p className="break-all text-base font-medium text-ink">{file.name}</p>
                  <p className="mt-2 font-mono text-xs text-muted">{formatBytes(file.size)} · Ready for validation</p>
                  <button className="secondary-button mt-6 pointer-events-auto" onClick={reset}><X className="h-4 w-4" /> Remove</button>
                </div>
              ) : (
                <div className="mt-6">
                  <h2 className="text-xl font-semibold tracking-tight text-ink">Drag and Drop File</h2>
                  <p className="mt-2 text-sm leading-6 text-muted">Drop a valid Windows PE here, or select one from your device.</p>
                  <button className="primary-button mt-6 pointer-events-auto" onClick={() => inputRef.current?.click()}>Select file</button>
                  <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.14em] text-muted">.exe · .dll · .sys · .scr · max {settings?.max_file_size_mb || 100} MB</p>
                </div>
              )}
              <input ref={inputRef} type="file" className="sr-only" onChange={(event) => chooseFile(event.target.files?.[0])} />
            </div>
          </div>
          {error && <div className="mt-4 flex items-start gap-3 rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-danger"><FileWarning className="mt-0.5 h-4 w-4 shrink-0" /><p>{error}</p></div>}
          {(phase === 'uploading' || phase === 'analyzing') && (
            <div className="mt-5 rounded-xl border border-accent/20 bg-accent/5 p-4">
              <div className="flex items-center justify-between text-xs"><span className="flex items-center gap-2 text-ink"><ScanLine className="h-4 w-4 animate-pulse text-accent" />{phase === 'uploading' ? 'Transferring file safely' : 'Extracting compatible features and classifying'}</span><span className="font-mono text-muted">{phase === 'uploading' ? `${progress}%` : 'PROCESSING'}</span></div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-canvas"><div className={`h-full rounded-full bg-accent transition-all ${phase === 'analyzing' ? 'animate-pulse-soft' : ''}`} style={{ width: `${phase === 'analyzing' ? 100 : progress}%` }} /></div>
            </div>
          )}
          {file && !['uploading', 'analyzing'].includes(phase) && !result && <button onClick={submit} className="primary-button mt-5 w-full justify-center py-3.5"><ScanLine className="h-4 w-4" /> Begin static analysis</button>}
        </section>
        <aside className="space-y-6">
          {result ? (
            <section className="panel p-6">
              <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl border border-success/25 bg-success/10 text-success"><CheckCircle2 className="h-5 w-5" /></div><div><p className="text-sm font-medium text-ink">Analysis recorded</p><p className="mt-0.5 text-xs text-muted">Event #{result.id}</p></div></div>
              <div className="my-6 h-px bg-line" />
              <StatusBadge value={result.classification || result.status} />
              <p className="mt-4 font-mono text-4xl font-semibold text-ink">{formatScore(result.score)}</p>
              <p className="mt-2 text-xs text-muted">Detection probability</p>
              {result.error_message && <p className="mt-4 rounded-lg border border-warning/20 bg-warning/10 p-3 text-xs leading-5 text-warning">{result.error_message}</p>}
              {result.cached_from_analysis_id && <p className="mt-4 text-xs leading-5 text-muted">Verified cached intelligence reused from analysis #{result.cached_from_analysis_id}; expensive engines were not run again.</p>}
              <Link className="primary-button mt-6 w-full justify-center" to={`/analyses/${result.id}`}>Open technical details</Link>
            </section>
          ) : (
            <section className="panel p-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">Analysis sequence</p>
              <ol className="mt-5 space-y-5">
                {['Validate PE structure', 'Calculate SHA-256 and check cache', 'Extract verified EMBER v2 features', 'Classify with XGBoost', 'Enrich priority results with llama3'].map((label, index) => (
                  <li key={label} className="flex gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full border border-line bg-elevated font-mono text-[10px] text-accent">{index + 1}</span><span className="pt-0.5 text-sm text-muted">{label}</span></li>
                ))}
              </ol>
            </section>
          )}
          <section className="rounded-2xl border border-line/70 bg-canvas/40 p-5"><p className="text-xs font-medium text-ink">Safety boundary</p><p className="mt-2 text-xs leading-5 text-muted">This workflow performs static analysis only. It does not run, delete, quarantine, or modify the submitted file.</p></section>
        </aside>
      </div>
    </>
  )
}

