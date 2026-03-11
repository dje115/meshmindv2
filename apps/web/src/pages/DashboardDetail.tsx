import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, BarChart3, Plus } from 'lucide-react'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function DashboardDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = id === 'new'

  return (
    <ErrorBoundary>
      <div>
        <button
          onClick={() => navigate('/dashboards')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboards
        </button>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">
          {isNew ? 'Create dashboard' : 'Dashboard'}
        </h1>
        <p className="text-slate-500 text-sm mb-8">
          {isNew
            ? 'Dashboard creation flow. Widget model and AI-generated dashboards planned.'
            : 'Dashboard detail and widgets.'}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="rounded-xl border border-dashed border-slate-700/60 bg-slate-900/30 p-8 text-center">
            <div className="inline-flex p-3 rounded-lg bg-slate-800/80 text-slate-500 mb-3">
              <BarChart3 className="w-8 h-8" />
            </div>
            <p className="text-sm text-slate-500 mb-2">Placeholder widget</p>
            <p className="text-xs text-slate-600">Future: charts, metrics, AI insights</p>
          </div>
          <button
            type="button"
            className="rounded-xl border border-dashed border-slate-600 p-8 flex flex-col items-center justify-center gap-2 text-slate-500 hover:text-slate-400 hover:border-slate-500 transition-colors"
          >
            <Plus className="w-8 h-8" />
            <span className="text-sm">Add widget</span>
          </button>
        </div>
      </div>
    </ErrorBoundary>
  )
}
