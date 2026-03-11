import { useNavigate } from 'react-router-dom'
import { Plus, BarChart3 } from 'lucide-react'
import { EmptyState } from '../components/EmptyState'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function DashboardsPage() {
  const navigate = useNavigate()
  const dashboards: { id: string; name: string }[] = [] // Placeholder - no backend yet

  return (
    <ErrorBoundary>
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Dashboards</h1>
            <p className="text-slate-500 text-sm mt-1">
              AI-powered analytics and widgets (coming soon)
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboards/new')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create dashboard
          </button>
        </div>
        {dashboards.length === 0 ? (
          <EmptyState
            icon={<BarChart3 className="w-14 h-14" />}
            title="No dashboards yet"
            description="Create dashboards to visualize knowledge base metrics, source coverage, and more. Widget-based layout with optional AI-generated insights."
            action={
              <button
                onClick={() => navigate('/dashboards/new')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium transition-colors"
              >
                <Plus className="w-4 h-4" />
                Create your first dashboard
              </button>
            }
            hint="Planned: publishable URLs, wallboard/public mode, per-dashboard permissions."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboards.map((d) => (
              <button
                key={d.id}
                onClick={() => navigate(`/dashboards/${d.id}`)}
                className="text-left p-5 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-800/50 transition-colors"
              >
                <BarChart3 className="w-8 h-8 text-slate-500 mb-3" />
                <h3 className="font-medium text-slate-200">{d.name}</h3>
              </button>
            ))}
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}
