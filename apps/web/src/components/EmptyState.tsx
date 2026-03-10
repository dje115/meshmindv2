import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      {icon && <div className="mb-4 text-slate-500">{icon}</div>}
      <h3 className="text-lg font-medium text-slate-200 mb-2">{title}</h3>
      {description && <p className="text-sm text-slate-500 max-w-md mb-6">{description}</p>}
      {action}
    </div>
  )
}
