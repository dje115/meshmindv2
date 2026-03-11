import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Bot,
  HelpCircle,
  X,
  CircleDot,
  CircleOff,
  AlertTriangle,
  Clock,
} from 'lucide-react'
import { agentsList, jobsList } from '../lib/api'
import { DataTable, type Column } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { ErrorBoundary } from '../components/ErrorBoundary'
import type { Agent } from '../lib/api'

function statusIcon(status: string) {
  switch (status) {
    case 'active':
      return <CircleDot className="w-4 h-4 text-emerald-400" aria-hidden />
    case 'stale':
      return <AlertTriangle className="w-4 h-4 text-amber-400" aria-hidden />
    case 'dead':
      return <CircleOff className="w-4 h-4 text-slate-500" aria-hidden />
    default:
      return <Clock className="w-4 h-4 text-slate-500" aria-hidden />
  }
}

export function AgentsPage() {
  const navigate = useNavigate()
  const [showHelp, setShowHelp] = useState(true)
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsList(),
    refetchInterval: 10000,
  })
  const { data: jobs = [] } = useQuery({
    queryKey: ['jobs', { limit: 100 }],
    queryFn: () => jobsList(undefined, undefined, 100),
  })

  const jobByAgent = new Map<string, typeof jobs[0]>()
  for (const j of jobs) {
    if (j.agent_id && !jobByAgent.has(j.agent_id)) {
      jobByAgent.set(j.agent_id, j)
    }
  }

  const columns: Column<Agent & { lastJob?: typeof jobs[0] }>[] = [
    {
      key: 'status',
      header: 'State',
      render: (r) => (
        <span className="flex items-center gap-2" title={r.status}>
          {statusIcon(r.status)}
          <span
            className={`capitalize ${r.status === 'active' ? 'text-emerald-400' : r.status === 'stale' ? 'text-amber-400' : 'text-slate-500'}`}
          >
            {r.status}
          </span>
        </span>
      ),
    },
    { key: 'name', header: 'Name' },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (r) => (
        <span className="text-slate-400 text-sm">
          {r.capabilities?.slice(0, 4).join(', ')}
          {(r.capabilities?.length ?? 0) > 4 && '…'}
        </span>
      ),
    },
    {
      key: 'last_heartbeat',
      header: 'Last heartbeat',
      render: (r) => (
        <span className="text-slate-500 text-sm" title={r.last_heartbeat}>
          {r.last_heartbeat ? new Date(r.last_heartbeat).toLocaleString() : '—'}
        </span>
      ),
    },
    {
      key: 'lastJob',
      header: 'Current/Last job',
      render: (r) => {
        const j = jobByAgent.get(r.id)
        if (!j) return <span className="text-slate-500">—</span>
        return (
          <span className="text-slate-400 text-sm">
            {j.job_kind ?? 'job'} · {j.status}
          </span>
        )
      },
    },
  ]

  const agentsWithJobs = agents.map((a) => ({
    ...a,
    lastJob: jobByAgent.get(a.id),
  }))

  return (
    <ErrorBoundary>
      <div>
        <div className="flex items-start justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Agents</h1>
            <p className="text-slate-500 text-sm mt-1">
              Workers that process documents, run OCR, embed, and more
            </p>
          </div>
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
            aria-expanded={showHelp}
          >
            <HelpCircle className="w-4 h-4" />
            {showHelp ? 'Hide' : 'Show'} help
          </button>
        </div>

        {showHelp && (
          <div className="mb-6 rounded-xl border border-slate-800/80 bg-slate-900/40 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold text-slate-200 mb-2">What is an agent?</h3>
                <p className="text-sm text-slate-400 mb-3 max-w-2xl">
                  Agents are worker processes (filesystem connector, OCR, image, embed) that register with MeshMind,
                  claim jobs, and process documents. They run separately from this control plane.
                </p>
                <h4 className="font-medium text-slate-300 text-sm mb-2">How to add an agent</h4>
                <ol className="list-decimal list-inside text-sm text-slate-400 space-y-1 mb-3">
                  <li>Install and run the worker (e.g. <code className="text-slate-500">meshmind-connectors</code> or <code className="text-slate-500">meshmind-worker-embed</code>)</li>
                  <li>Point it at this control API URL</li>
                  <li>It will register, appear here, and start claiming jobs</li>
                </ol>
                <p className="text-xs text-slate-500">
                  Host/machine info is not yet exposed by the API.
                </p>
              </div>
              <button
                onClick={() => setShowHelp(false)}
                className="p-1 rounded text-slate-500 hover:text-slate-300"
                aria-label="Close help"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {agents.length === 0 && !isLoading ? (
          <EmptyState
            icon={<Bot className="w-14 h-14" />}
            title="No agents registered"
            description="Start worker processes (filesystem, OCR, embed, etc.) and point them at this control API. They will register automatically."
            hint="Agents must be running on your network with the correct API URL and credentials."
          />
        ) : (
          <DataTable
            columns={columns}
            data={agentsWithJobs}
            keyExtractor={(r) => r.id}
            onRowClick={(r) => navigate(`/agents/${r.id}`)}
            emptyMessage="No agents."
            isLoading={isLoading}
          />
        )}
      </div>
    </ErrorBoundary>
  )
}
