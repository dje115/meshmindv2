import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { sourcesList, workspacesList } from '../lib/api'
import { DataTable, type Column } from '../components/DataTable'
import { ErrorBoundary } from '../components/ErrorBoundary'
import type { Source } from '../lib/api'

export function SourcesPage() {
  const navigate = useNavigate()
  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => sourcesList(),
  })
  const { data: workspaces = [] } = useQuery({
    queryKey: ['workspaces'],
    queryFn: workspacesList,
  })
  const wsMap = Object.fromEntries(workspaces.map((w) => [w.id, w.name]))

  const columns: Column<Source>[] = [
    { key: 'name', header: 'Name' },
    {
      key: 'kind',
      header: 'Kind',
      render: (r) => (
        <span className="capitalize">{r.kind}</span>
      ),
    },
    {
      key: 'workspace_id',
      header: 'Workspace',
      render: (r) => wsMap[r.workspace_id] ?? r.workspace_id,
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <span
          className={`inline-flex px-2 py-0.5 rounded text-xs ${
            r.status === 'completed' ? 'bg-emerald-900/50 text-emerald-300' :
            r.status === 'failed' ? 'bg-red-900/50 text-red-300' :
            'bg-slate-700/50 text-slate-400'
          }`}
        >
          {r.status}
        </span>
      ),
    },
  ]

  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Sources</h1>
        <DataTable
          columns={columns}
          data={sources}
          keyExtractor={(r) => r.id}
          onRowClick={(r) => navigate(`/sources/${r.id}`)}
          emptyMessage="No sources. Add a source to get started."
          isLoading={isLoading}
        />
      </div>
    </ErrorBoundary>
  )
}
