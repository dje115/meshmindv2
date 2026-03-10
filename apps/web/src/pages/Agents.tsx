import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { agentsList } from '../lib/api'
import { DataTable, type Column } from '../components/DataTable'
import { ErrorBoundary } from '../components/ErrorBoundary'
import type { Agent } from '../lib/api'

export function AgentsPage() {
  const navigate = useNavigate()
  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsList(),
    refetchInterval: 10000,
  })

  const columns: Column<Agent>[] = [
    { key: 'name', header: 'Name' },
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <span
          className={`inline-flex px-2 py-0.5 rounded text-xs ${
            r.status === 'active' ? 'bg-emerald-900/50 text-emerald-300' :
            r.status === 'stale' ? 'bg-amber-900/50 text-amber-300' :
            'bg-slate-700/50 text-slate-400'
          }`}
        >
          {r.status}
        </span>
      ),
    },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (r) => (
        <span className="text-slate-400">
          {r.capabilities?.slice(0, 3).join(', ')}
          {(r.capabilities?.length ?? 0) > 3 && '…'}
        </span>
      ),
    },
    {
      key: 'last_heartbeat',
      header: 'Last heartbeat',
      render: (r) =>
        r.last_heartbeat
          ? new Date(r.last_heartbeat).toLocaleString()
          : '—',
    },
  ]

  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Agents</h1>
        <DataTable
          columns={columns}
          data={agents}
          keyExtractor={(r) => r.id}
          onRowClick={(r) => navigate(`/agents/${r.id}`)}
          emptyMessage="No agents registered."
          isLoading={isLoading}
        />
      </div>
    </ErrorBoundary>
  )
}
