import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  FolderOpen,
  Briefcase,
  Bot,
  Plus,
  MessageSquare,
  Search,
  ArrowRight,
  BarChart3,
  Server,
  RefreshCw,
  Copy,
  Check,
} from 'lucide-react'
import { sourcesList, jobsList, agentsList, componentsStatus } from '../lib/api'
import type { ComponentsStatusResponse } from '../lib/api'
import { Loading } from '../components/Loading'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { EmptyState } from '../components/EmptyState'

const COMPONENT_COMMANDS: Record<string, string> = {
  control_api: 'cargo run -p meshmind-control-api',
  query_api: 'cd apps/query-api && python -m uvicorn meshmind_query_api.main:app --host 0.0.0.0 --port 3001',
  ollama: 'ollama serve',
  qdrant: 'docker run -p 6333:6333 qdrant/qdrant',
  database: 'docker compose -f infrastructure/docker-compose.infra.yml up -d postgres',
}

export function Overview() {
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const {
    data: components,
    isLoading: componentsLoading,
    isError: componentsError,
    refetch: refetchComponents,
  } = useQuery({
    queryKey: ['components'],
    queryFn: componentsStatus,
    retry: false,
  })
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

  const copyCommand = (id: string, cmd: string) => {
    navigator.clipboard.writeText(cmd)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const recentJobs = jobs.slice(0, 5)
  const completed = jobs.filter((j) => j.status === 'completed').length
  const failed = jobs.filter((j) => j.status === 'failed').length
  const active = agents.filter((a) => a.status === 'active').length
  const isLoading = sourcesLoading || jobsLoading || agentsLoading

  return (
    <ErrorBoundary>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Command centre</h1>
          <p className="text-slate-400 text-sm">
            Monitor your knowledge base, agents, and jobs at a glance.
          </p>
        </div>

        <section className="rounded-xl border border-slate-800/80 bg-slate-900/40 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
            <h2 className="font-semibold text-slate-200 flex items-center gap-2">
              <Server className="w-5 h-5 text-slate-400" />
              Component status
            </h2>
            <button
              onClick={() => refetchComponents()}
              disabled={componentsLoading}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${componentsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          <div className="p-5">
            {componentsLoading ? (
              <div className="py-4">
                <Loading />
              </div>
            ) : componentsError || !components ? (
              <p className="py-4 text-slate-500 text-sm">
                Could not load component status
                {componentsError && (
                  <span className="block mt-1 text-red-400 text-xs">
                    {(componentsError as Error)?.message}
                  </span>
                )}
                .{" "}
                <button
                  type="button"
                  onClick={() => refetchComponents()}
                  className="text-sky-400 hover:text-sky-300"
                >
                  Retry
                </button>
              </p>
            ) : (
              <ComponentsStatusGrid
                components={components}
                onCopyCommand={copyCommand}
                copiedId={copiedId}
              />
            )}
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            icon={<FolderOpen className="w-5 h-5" />}
            label="Sources"
            value={sourcesLoading ? '—' : sources.length}
            href="/sources"
            actionLabel="Add source"
          />
          <StatCard
            icon={<Briefcase className="w-5 h-5" />}
            label="Jobs"
            value={
              jobsLoading
                ? '—'
                : `${completed} completed${failed ? `, ${failed} failed` : ''}`
            }
            href="/jobs"
          />
          <StatCard
            icon={<Bot className="w-5 h-5" />}
            label="Active agents"
            value={agentsLoading ? '—' : `${active} of ${agents.length}`}
            href="/agents"
          />
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
              <h2 className="font-semibold text-slate-200">Quick actions</h2>
            </div>
            <div className="p-5 grid gap-3">
              <Link
                to="/sources"
                className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors group"
              >
                <div className="p-2 rounded-lg bg-sky-500/20 text-sky-400">
                  <Plus className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-200">Add a source</p>
                  <p className="text-sm text-slate-500">Connect files, databases, or APIs</p>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-slate-400" />
              </Link>
              <Link
                to="/ask"
                className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors group"
              >
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-200">Ask a question</p>
                  <p className="text-sm text-slate-500">Chat with your knowledge base</p>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-slate-400" />
              </Link>
              <Link
                to="/search"
                className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors group"
              >
                <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
                  <Search className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-200">Search</p>
                  <p className="text-sm text-slate-500">Find documents and chunks</p>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-slate-400" />
              </Link>
              <Link
                to="/dashboards"
                className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors group"
              >
                <div className="p-2 rounded-lg bg-violet-500/20 text-violet-400">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-200">Dashboards</p>
                  <p className="text-sm text-slate-500">View analytics and widgets</p>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-slate-400" />
              </Link>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
              <h2 className="font-semibold text-slate-200">Recent jobs</h2>
              <Link
                to="/jobs"
                className="text-sm text-sky-400 hover:text-sky-300 transition-colors"
              >
                View all
              </Link>
            </div>
            <div className="min-h-[200px]">
              {jobsLoading ? (
                <div className="p-8">
                  <Loading />
                </div>
              ) : recentJobs.length === 0 ? (
                <EmptyState
                  icon={<Briefcase className="w-14 h-14" />}
                  title="No jobs yet"
                  description="Jobs are created when you ingest sources. Add a source to get started."
                  action={
                    <Link
                      to="/sources"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Add source
                    </Link>
                  }
                />
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800/80 bg-slate-800/30">
                      <th className="px-5 py-3 text-left font-medium text-slate-400">Status</th>
                      <th className="px-5 py-3 text-left font-medium text-slate-400">Kind</th>
                      <th className="px-5 py-3 text-left font-medium text-slate-400">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {recentJobs.map((j) => (
                      <tr key={j.id} className="hover:bg-slate-800/30">
                        <td className="px-5 py-3">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${
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
                        <td className="px-5 py-3 text-slate-300">{j.job_kind ?? '—'}</td>
                        <td className="px-5 py-3 text-slate-500">
                          {new Date(j.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </section>

        {!isLoading && sources.length === 0 && agents.length === 0 && (
          <div className="rounded-xl border border-sky-800/50 bg-sky-950/30 p-6">
            <h3 className="font-semibold text-sky-200 mb-2">Get started</h3>
            <p className="text-sm text-slate-400 mb-4 max-w-xl">
              MeshMind is ready. Add a filesystem source, then run workers to ingest and embed your documents.
              Agents must be running separately to process jobs.
            </p>
            <Link
              to="/sources"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add your first source
            </Link>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}

function ComponentsStatusGrid({
  components,
  onCopyCommand,
  copiedId,
}: {
  components: ComponentsStatusResponse
  onCopyCommand: (id: string, cmd: string) => void
  copiedId: string | null
}) {
  const items: { id: string; label: string; status: typeof components.control_api; command?: string }[] = [
    { id: 'control_api', label: 'Control API', status: components.control_api, command: COMPONENT_COMMANDS.control_api },
    { id: 'database', label: 'Database', status: components.database, command: COMPONENT_COMMANDS.database },
    { id: 'query_api', label: 'Query API', status: components.query_api, command: COMPONENT_COMMANDS.query_api },
    { id: 'ollama', label: 'Ollama', status: components.ollama, command: COMPONENT_COMMANDS.ollama },
    { id: 'qdrant', label: 'Qdrant', status: components.qdrant, command: COMPONENT_COMMANDS.qdrant },
  ]
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {items.map(({ id, label, status, command }) => (
        <div
          key={id}
          className="rounded-lg border border-slate-700/60 bg-slate-800/30 p-4 flex flex-col gap-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-200">{label}</span>
            <span
              className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                status.status === 'ok' ? 'bg-emerald-900/50 text-emerald-300' : 'bg-red-900/50 text-red-300'
              }`}
            >
              {status.status === 'ok' ? 'Running' : 'Down'}
            </span>
          </div>
          {status.message && (
            <p className="text-xs text-red-400 truncate" title={status.message}>
              {status.message}
            </p>
          )}
          {command && status.status !== 'ok' && (
            <div className="mt-auto flex items-center gap-1">
              <code className="flex-1 text-xs text-slate-500 truncate px-2 py-1 bg-slate-900/50 rounded">
                {command}
              </code>
              <button
                type="button"
                onClick={() => onCopyCommand(id, command)}
                className="p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors"
                title="Copy command"
              >
                {copiedId === id ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  href,
  actionLabel,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  href?: string
  actionLabel?: string
}) {
  const content = (
    <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-5 flex items-center gap-4">
      <div className="p-2.5 rounded-lg bg-slate-800/80 text-slate-400">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-xl font-semibold text-slate-100">{value}</p>
      </div>
    </div>
  )
  if (href) {
    return (
      <Link to={href} className="block group">
        {content}
        {actionLabel && (
          <p className="mt-2 text-xs text-sky-400 group-hover:text-sky-300 transition-colors">
            {actionLabel} →
          </p>
        )}
      </Link>
    )
  }
  return content
}
