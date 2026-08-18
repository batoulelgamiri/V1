export function ActivityBars({ activity = [] }) {
  const maximum = Math.max(1, ...activity.map((item) => item.count))
  return (
    <div className="flex h-44 items-end gap-2 sm:gap-3" aria-label="Analysis activity over seven days">
      {activity.map((item) => (
        <div key={item.date} className="group flex min-w-0 flex-1 flex-col items-center gap-2">
          <div className="relative flex h-32 w-full items-end overflow-hidden rounded-lg bg-canvas/55">
            <div
              className="w-full rounded-lg border border-accent/20 bg-gradient-to-t from-accent/25 to-accent/75 transition-all duration-500 group-hover:to-accent"
              style={{ height: `${Math.max(item.count ? 12 : 3, (item.count / maximum) * 100)}%` }}
            />
            <span className="absolute inset-x-0 top-2 text-center font-mono text-[10px] text-muted opacity-0 transition-opacity group-hover:opacity-100">{item.count}</span>
          </div>
          <span className="font-mono text-[9px] uppercase tracking-wide text-muted">{new Date(`${item.date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short' })}</span>
        </div>
      ))}
    </div>
  )
}

