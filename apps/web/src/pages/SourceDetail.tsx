import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Play, TestTube } from 'lucide-react'
import { sourcesList, sourceIngest } from '../lib/api'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function SourceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  const source = sources.find((s) => s.id === id)

  const ingestMut = useMutation({
    mutationFn: () => sourceIngest(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      navigate('/jobs')
    },
  })

  if (!source && sources.length > 0) {
    return <p className="text-slate-500">Source not found.</p>
  }

  const config = (source?.config ?? {}) as Record<string, unknown>
  const path = (config.path ?? config.root_path ?? '—') as string

  return (
    <ErrorBoundary>
      <div className="max-w-2xl">
        <button
          onClick={() => navigate('/sources')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Sources
        </button>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">{source?.name ?? 'Source'}</h1>
        <p className="text-slate-500 text-sm mb-6">
          {source?.kind} source · {source?.status}
        </p>
        {source && (
          <>
            <div className="space-y-4 mb-8">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Path</p>
                <p className="text-slate-200 font-mono text-sm">{path}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Status</p>
                <span
                  className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${
                    source.status === 'completed' ? 'bg-emerald-900/50 text-emerald-300' :
                    source.status === 'failed' ? 'bg-red-900/50 text-red-300' :
                    'bg-slate-700/50 text-slate-400'
                  }`}
                >
                  {source.status}
                </span>
              </div>
            </div>
            <div className="flex flex-wrap gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/40">
              <button
                type="button"
                disabled
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700/60 text-slate-500 text-sm font-medium cursor-not-allowed"
                title="Not yet implemented"
              >
                <TestTube className="w-4 h-4" /> Test connection
              </button>
              <button
                type="button"
                onClick={() => ingestMut.mutate()}
                disabled={ingestMut.isPending || !id}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Create a scan job for workers to claim"
              >
                <Play className="w-4 h-4" /> {ingestMut.isPending ? 'Starting…' : 'Ingest now'}
              </button>
              {ingestMut.error && (
                <p className="text-xs text-red-400 self-center">{String(ingestMut.error.message)}</p>
              )}
              {ingestMut.isSuccess && (
                <p className="text-xs text-emerald-400 self-center">Job created. Check Jobs for progress.</p>
              )}
              <p className="text-xs text-slate-500 self-center">
                Workers must be running to process the job. Ingest creates a job that filesystem workers claim.
              </p>
            </div>
          </>
        )}
      </div>
    </ErrorBoundary>
  )
}
