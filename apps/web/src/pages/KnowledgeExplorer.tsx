import { useQuery } from '@tanstack/react-query'
import { sourcesList } from '../lib/api'
import { EmptyState } from '../components/EmptyState'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { Compass } from 'lucide-react'

export function KnowledgeExplorerPage() {
  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Knowledge Explorer</h1>
        <p className="text-slate-500 mb-8 max-w-2xl">
          Explore indexed content by source. Use Search and Ask to query your knowledge base.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map((s) => (
            <div
              key={s.id}
              className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 hover:border-slate-600 transition-colors"
            >
              <h3 className="font-medium text-slate-200">{s.name}</h3>
              <p className="text-sm text-slate-500 mt-1 capitalize">{s.kind}</p>
              <span
                className={`inline-block mt-2 px-2 py-0.5 rounded text-xs ${
                  s.status === 'completed' ? 'bg-emerald-900/50 text-emerald-300' : 'bg-slate-700/50 text-slate-400'
                }`}
              >
                {s.status}
              </span>
            </div>
          ))}
        </div>
        {sources.length === 0 && (
          <EmptyState
            icon={<Compass className="w-12 h-12" />}
            title="No sources yet"
            description="Add sources and ingest documents to build your knowledge base."
          />
        )}
      </div>
    </ErrorBoundary>
  )
}
