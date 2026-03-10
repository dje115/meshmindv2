import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { jobsList, sourcesList } from '../lib/api'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: jobs = [] } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsList(undefined, undefined, 100),
  })
  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  const job = jobs.find((j) => j.id === id)
  const source = job ? sources.find((s) => s.id === job.source_id) : null

  return (
    <ErrorBoundary>
      <div>
        <button
          onClick={() => navigate('/jobs')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Jobs
        </button>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">
          Job {job?.id?.slice(0, 8) ?? '—'}
        </h1>
        {job && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Status</p>
              <p className="text-slate-200">{job.status}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Kind</p>
              <p className="text-slate-200">{job.job_kind ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Source</p>
              <p className="text-slate-200">{source?.name ?? job.source_id}</p>
            </div>
            {job.error && (
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Error</p>
                <p className="text-red-400 text-sm">{job.error}</p>
              </div>
            )}
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Created</p>
              <p className="text-slate-400">{new Date(job.created_at).toLocaleString()}</p>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}
