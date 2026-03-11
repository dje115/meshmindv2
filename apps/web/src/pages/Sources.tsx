import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, FolderOpen } from 'lucide-react'
import { sourcesList, workspacesList } from '../lib/api'
import { DataTable, type Column } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
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
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Sources</h1>
            <p className="text-slate-500 text-sm mt-1">Connect files, databases, and APIs to your knowledge base</p>
          </div>
          <Link
            to="/sources/add"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add source
          </Link>
        </div>
        {sources.length === 0 && !isLoading ? (
          <EmptyState
            icon={<FolderOpen className="w-14 h-14" />}
            title="No sources yet"
            description="Add a filesystem, database, or other source to start ingesting documents."
            action={
              <Link
                to="/sources/add"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add your first source
              </Link>
            }
            hint="Filesystem sources require a path. Workers will scan and process documents when ingest is triggered."
          />
        ) : (
          <DataTable
            columns={columns}
            data={sources}
            keyExtractor={(r) => r.id}
            onRowClick={(r) => navigate(`/sources/${r.id}`)}
            emptyMessage="No sources."
            isLoading={isLoading}
          />
        )}
      </div>
    </ErrorBoundary>
  )
}
