import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { jobsList, sourcesList } from '../lib/api'
import { DataTable, type Column } from '../components/DataTable'
import { ErrorBoundary } from '../components/ErrorBoundary'
import type { Job } from '../lib/api'

export function JobsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: () => jobsList(undefined, statusFilter || undefined, 50),
  })
  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  const srcMap = Object.fromEntries(sources.map((s) => [s.id, s.name]))

  const columns: Column<Job>[] = [
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <span
          className={`inline-flex px-2 py-0.5 rounded text-xs ${
            r.status === 'completed' ? 'bg-emerald-900/50 text-emerald-300' :
            r.status === 'failed' ? 'bg-red-900/50 text-red-300' :
            r.status === 'claimed' ? 'bg-sky-900/50 text-sky-300' :
            'bg-slate-700/50 text-slate-400'
          }`}
        >
          {r.status}
        </span>
      ),
    },
    { key: 'job_kind', header: 'Kind', render: (r) => r.job_kind ?? '—' },
    {
      key: 'source_id',
      header: 'Source',
      render: (r) => srcMap[r.source_id] ?? r.source_id,
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (r) => new Date(r.created_at).toLocaleString(),
    },
    {
      key: 'error',
      header: 'Error',
      render: (r) =>
        r.error ? (
          <span className="text-red-400 text-xs truncate max-w-[200px] block">
            {r.error}
          </span>
        ) : (
          '—'
        ),
    },
  ]

  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Jobs</h1>
        <div className="flex gap-2 mb-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-md bg-slate-800 border border-slate-600 text-slate-200"
          >
            <option value="">All statuses</option>
            <option value="queued">Queued</option>
            <option value="claimed">Claimed</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
        <DataTable
          columns={columns}
          data={jobs}
          keyExtractor={(r) => r.id}
          onRowClick={(r) => navigate(`/jobs/${r.id}`)}
          emptyMessage="No jobs."
          isLoading={isLoading}
        />
      </div>
    </ErrorBoundary>
  )
}
