import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { agentsList } from '../lib/api'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function AgentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsList(),
    refetchInterval: 10000,
  })
  const agent = agents.find((a) => a.id === id)

  return (
    <ErrorBoundary>
      <div>
        <button
          onClick={() => navigate('/agents')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Agents
        </button>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">
          {agent?.name ?? 'Agent'}
        </h1>
        {agent && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Status</p>
              <p className="text-slate-200">{agent.status}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Capabilities</p>
              <p className="text-slate-400">{agent.capabilities?.join(', ')}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Last heartbeat</p>
              <p className="text-slate-400">
                {agent.last_heartbeat ? new Date(agent.last_heartbeat).toLocaleString() : '—'}
              </p>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}
