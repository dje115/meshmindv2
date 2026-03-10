export function Loading({ className = '' }: { className?: string }) {
  return (
    <div
      className={`flex items-center justify-center p-12 ${className}`}
      role="status"
      aria-label="Loading"
    >
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-600 border-t-sky-500" />
    </div>
  )
}

export function LoadingDots() {
  return (
    <span className="inline-flex gap-1" role="status" aria-label="Loading">
      <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce [animation-delay:-0.3s]" />
      <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce [animation-delay:-0.15s]" />
      <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" />
    </span>
  )
}
