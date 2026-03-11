import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  /** Secondary hint below the action */
  hint?: string
}

export function EmptyState({ icon, title, description, action, hint }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-8 text-center rounded-xl border border-dashed border-slate-700/60 bg-slate-900/30">
      {icon && <div className="mb-5 text-slate-500 [&>svg]:w-14 [&>svg]:h-14">{icon}</div>}
      <h3 className="text-lg font-semibold text-slate-200 mb-2">{title}</h3>
      {description && <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">{description}</p>}
      {action && <div className="mb-4">{action}</div>}
      {hint && <p className="text-xs text-slate-500 max-w-sm">{hint}</p>}
    </div>
  )
}
