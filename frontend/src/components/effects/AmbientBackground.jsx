import { useEffect } from 'react'

export function AmbientBackground() {
  useEffect(() => {
    const update = (event) => {
      document.documentElement.style.setProperty('--cursor-x', `${event.clientX}px`)
      document.documentElement.style.setProperty('--cursor-y', `${event.clientY}px`)
    }
    window.addEventListener('pointermove', update, { passive: true })
    return () => window.removeEventListener('pointermove', update)
  }, [])

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="ambient-grid absolute inset-0" />
      <div className="cursor-aura absolute inset-0" />
      <div className="absolute inset-x-0 top-0 h-px animate-scan-slow bg-gradient-to-r from-transparent via-accent/40 to-transparent" />
    </div>
  )
}

