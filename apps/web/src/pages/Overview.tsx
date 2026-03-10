import { useQuery } from '@tanstack/react-query'
import { FolderOpen, Briefcase, Bot } from 'lucide-react'
import { sourcesList, jobsList, agentsList } from '../lib/api'
import { Loading } from '../components/Loading'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function Overview() {
  const { data: sources = [], isLoading: sourcesLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', { limit: 10 }],
    queryFn: () => jobsList(undefined, undefined, 10),
  })
  const { data: agents = [], isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsList(),
  })

  const recentJobs = jobs.slice(0, 5)
  const completed = jobs.filter((j) => j.status === 'completed').length
  const failed = jobs.filter((j) => j.status === 'failed').length
  const active = agents.filter((a) => a.status === 'active').length

  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Overview</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<FolderOpen className="w-5 h-5" />}
            label="Sources"
            value={sourcesLoading ? '—' : sources.length}
          />
          <StatCard
            icon={<Briefcase className="w-5 h-5" />}
            label="Jobs"
            value={jobsLoading ? '—' : `${completed} completed${failed ? `, ${failed} failed` : ''}`}
          />
          <StatCard
            icon={<Bot className="w-5 h-5" />}
            label="Active Agents"
            value={agentsLoading ? '—' : active}
          />
        </div>
        <section>
          <h2 className="text-lg font-semibold text-slate-200 mb-4">Recent Jobs</h2>
          {jobsLoading ? (
            <Loading />
          ) : recentJobs.length === 0 ? (
            <p className="text-slate-500 py-8">No jobs yet.</p>
          ) : (
            <div className="rounded-lg border border-slate-700/50 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50 bg-slate-800/30">
                    <th className="px-4 py-3 text-left font-medium text-slate-300">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-300">Kind</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-300">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {recentJobs.map((j) => (
                    <tr key={j.id}>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                            j.status === 'completed'
                              ? 'bg-emerald-900/50 text-emerald-300'
                              : j.status === 'failed'
                                ? 'bg-red-900/50 text-red-300'
                                : 'bg-slate-700/50 text-slate-400'
                          }`}
                        >
                          {j.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{j.job_kind ?? '—'}</td>
                      <td className="px-4 py-3 text-slate-500">
                        {new Date(j.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </ErrorBoundary>
  )
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
}) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 flex items-center gap-4">
      <div className="text-slate-500">{icon}</div>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-xl font-semibold text-slate-100">{value}</p>
      </div>
    </div>
  )
}
