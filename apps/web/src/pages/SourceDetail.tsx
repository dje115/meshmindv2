import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { sourcesList } from '../lib/api'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function SourceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  const source = sources.find((s) => s.id === id)

  if (!source && sources.length > 0) {
    return <p className="text-slate-500">Source not found.</p>
  }

  return (
    <ErrorBoundary>
      <div>
        <button
          onClick={() => navigate('/sources')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Sources
        </button>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">
          {source?.name ?? 'Source'}
        </h1>
        {source && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Kind</p>
              <p className="text-slate-200">{source.kind}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Status</p>
              <p className="text-slate-200">{source.status}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">ID</p>
              <p className="text-slate-500 font-mono text-sm">{source.id}</p>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}
