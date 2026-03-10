import { ErrorBoundary } from '../components/ErrorBoundary'

export function SettingsPage() {
  return (
    <ErrorBoundary>
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Settings</h1>
        <p className="text-slate-500 mb-8 max-w-2xl">
          Application and workspace settings. Aligned with the UI-first settings direction —
          operational settings will move here from env/config as phases progress.
        </p>
        <div className="space-y-6 max-w-2xl">
          <section className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-6">
            <h2 className="font-semibold text-slate-200 mb-4">General</h2>
            <p className="text-slate-500 text-sm">General application preferences. (Planned)</p>
          </section>
          <section className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-6">
            <h2 className="font-semibold text-slate-200 mb-4">Document Processing</h2>
            <p className="text-slate-500 text-sm">Tika endpoint, OCR toggles. (Planned)</p>
          </section>
          <section className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-6">
            <h2 className="font-semibold text-slate-200 mb-4">Models</h2>
            <p className="text-slate-500 text-sm">Embedding and LLM model selection. (Planned)</p>
          </section>
          <section className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-6">
            <h2 className="font-semibold text-slate-200 mb-4">Web Research</h2>
            <p className="text-slate-500 text-sm">Web/internet research policy and controls. (Future)</p>
          </section>
        </div>
      </div>
    </ErrorBoundary>
  )
}
