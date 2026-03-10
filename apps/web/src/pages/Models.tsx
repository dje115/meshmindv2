import { ErrorBoundary } from '../components/ErrorBoundary'

export function ModelsPage() {
  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Models</h1>
        <p className="text-slate-500 mb-6 max-w-2xl">
          Model configuration (embedding and LLM) is managed via environment variables.
          A Settings UI for model selection is planned.
        </p>
        <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-6 max-w-xl">
          <h3 className="font-medium text-slate-200 mb-2">Current configuration</h3>
          <ul className="text-sm text-slate-400 space-y-1">
            <li>MESHMIND_EMBED_MODEL — embedding model (e.g. all-MiniLM-L6-v2)</li>
            <li>MESHMIND_ASK_MODEL — LLM for Ask (e.g. llama3.2)</li>
          </ul>
        </div>
      </div>
    </ErrorBoundary>
  )
}
