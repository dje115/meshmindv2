import { useQuery } from '@tanstack/react-query'
import { workspacesList } from '../lib/api'
import { DataTable, type Column } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { ErrorBoundary } from '../components/ErrorBoundary'
import type { Workspace } from '../lib/api'
import { Building2 } from 'lucide-react'

export function WorkspacesPage() {
  const { data: workspaces = [], isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: workspacesList,
  })

  const columns: Column<Workspace>[] = [
    { key: 'name', header: 'Name' },
    { key: 'slug', header: 'Slug' },
    { key: 'description', header: 'Description', render: (r) => r.description ?? '—' },
  ]

  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Workspaces & Permissions</h1>
        <p className="text-slate-500 mb-6 max-w-2xl">
          Workspaces organize sources. Permissions are managed per workspace and role.
        </p>
        <DataTable
          columns={columns}
          data={workspaces}
          keyExtractor={(r) => r.id}
          emptyMessage="No workspaces."
          isLoading={isLoading}
        />
        {workspaces.length === 0 && !isLoading && (
          <EmptyState
            icon={<Building2 className="w-12 h-12" />}
            title="No workspaces"
            description="A default workspace is usually created during setup."
          />
        )}
      </div>
    </ErrorBoundary>
  )
}
