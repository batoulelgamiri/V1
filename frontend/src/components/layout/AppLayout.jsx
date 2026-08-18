import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  Activity,
  FileClock,
  Menu,
  Moon,
  Radar,
  ScanLine,
  Settings,
  ShieldCheck,
  Sun,
  X,
} from 'lucide-react'
import { AmbientBackground } from '../effects/AmbientBackground'
import { useApi } from '../../hooks/useApi'

const navigation = [
  { to: '/', label: 'Overview', icon: Activity },
  { to: '/analyze', label: 'Manual analysis', icon: ScanLine },
  { to: '/wazuh', label: 'Wazuh detections', icon: Radar },
  { to: '/history', label: 'Analysis history', icon: FileClock },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid h-10 w-10 place-items-center rounded-xl border border-accent/30 bg-accent/10 text-accent shadow-glow">
        <ShieldCheck className="h-5 w-5" />
        <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-success ring-2 ring-surface" />
      </div>
      <div>
        <p className="font-semibold tracking-[0.12em] text-ink">AEGIS</p>
        <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-muted">PE Intelligence</p>
      </div>
    </div>
  )
}

function Sidebar({ open, close }) {
  return (
    <>
      {open && <button className="fixed inset-0 z-30 bg-black/45 lg:hidden" onClick={close} aria-label="Close navigation overlay" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-line/70 bg-surface/95 p-5 backdrop-blur-xl transition-transform duration-300 lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between">
          <Brand />
          <button className="icon-button lg:hidden" onClick={close} aria-label="Close navigation"><X className="h-5 w-5" /></button>
        </div>
        <div className="my-7 h-px bg-gradient-to-r from-accent/40 via-line to-transparent" />
        <nav className="space-y-1.5" aria-label="Primary navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={close}
              className={({ isActive }) => `group flex items-center gap-3 rounded-xl border px-3 py-3 text-sm transition-all ${isActive ? 'border-accent/25 bg-accent/10 text-ink shadow-glow' : 'border-transparent text-muted hover:border-line hover:bg-elevated/60 hover:text-ink'}`}
            >
              <Icon className="h-[18px] w-[18px] text-current" />
              <span>{label}</span>
              <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent opacity-0 transition-opacity group-[.active]:opacity-100" />
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto rounded-xl border border-line bg-canvas/55 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-ink">
            <span className="h-2 w-2 animate-pulse-soft rounded-full bg-success" /> Static analysis only
          </div>
          <p className="text-xs leading-5 text-muted">Files are inspected, never executed. No remediation actions are performed.</p>
        </div>
      </aside>
    </>
  )
}

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('aegis-theme') || 'dark')
  const { data: health } = useApi('/health')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('aegis-theme', theme)
  }, [theme])

  return (
    <div className="min-h-screen text-ink">
      <AmbientBackground />
      <Sidebar open={menuOpen} close={() => setMenuOpen(false)} />
      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-16 items-center border-b border-line/60 bg-canvas/75 px-4 backdrop-blur-xl sm:px-6 lg:px-10">
          <button className="icon-button mr-3 lg:hidden" onClick={() => setMenuOpen(true)} aria-label="Open navigation"><Menu className="h-5 w-5" /></button>
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            <span className={`h-2 w-2 rounded-full ${health?.model_available ? 'bg-success' : 'bg-warning'}`} />
            {health?.model_available ? 'Detection engine ready' : 'Model setup required'}
          </div>
          <button
            className="icon-button ml-auto"
            onClick={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </header>
        <main className="mx-auto max-w-[1500px] p-4 sm:p-6 lg:p-10"><Outlet /></main>
      </div>
    </div>
  )
}

