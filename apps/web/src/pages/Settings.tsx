import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsGet, settingsUpdate } from '../lib/api'
import { ErrorBoundary } from '../components/ErrorBoundary'

function str(v: unknown): string {
  if (v == null) return ''
  return String(v)
}

function num(v: unknown): number {
  if (v == null) return 0
  if (typeof v === 'number') return v
  const n = parseFloat(String(v))
  return isNaN(n) ? 0 : n
}

function bool(v: unknown): boolean {
  if (v == null) return false
  if (typeof v === 'boolean') return v
  const s = String(v).toLowerCase()
  return s === 'true' || s === '1' || s === 'yes'
}

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { data: all, isLoading, error } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsGet,
    retry: false,
  })

  const updateMut = useMutation({
    mutationFn: ({ category, settings }: { category: string; settings: Record<string, unknown> }) =>
      settingsUpdate(category, settings),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
  })

  if (isLoading || !all) {
    return (
      <ErrorBoundary>
        <div className="max-w-2xl">
          <h1 className="text-2xl font-bold text-slate-100 mb-2">Settings</h1>
          <p className="text-slate-500 text-sm">Loading…</p>
        </div>
      </ErrorBoundary>
    )
  }

  if (error) {
    return (
      <ErrorBoundary>
        <div className="max-w-2xl">
          <h1 className="text-2xl font-bold text-slate-100 mb-2">Settings</h1>
          <p className="text-red-400 text-sm">Failed to load settings: {String((error as Error).message)}</p>
        </div>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Settings</h1>
        <p className="text-slate-500 text-sm mb-8">
          Configure operational preferences. Changes apply immediately where supported.
        </p>
        <div className="space-y-4">
          <ModelsSection
            settings={all.models ?? {}}
            onSave={(s) => updateMut.mutate({ category: 'models', settings: s })}
            isPending={updateMut.isPending}
            error={updateMut.error?.message}
          />
          <InternetResearchSection
            settings={all.internet_research ?? {}}
            onSave={(s) => updateMut.mutate({ category: 'internet_research', settings: s })}
            isPending={updateMut.isPending}
            error={updateMut.error?.message}
          />
          <DocumentProcessingSection
            settings={all.document_processing ?? {}}
            onSave={(s) => updateMut.mutate({ category: 'document_processing', settings: s })}
            isPending={updateMut.isPending}
            error={updateMut.error?.message}
          />
          <ChatMemorySection
            settings={all.chat_memory ?? {}}
            onSave={(s) => updateMut.mutate({ category: 'chat_memory', settings: s })}
            isPending={updateMut.isPending}
            error={updateMut.error?.message}
          />
          <WorkersJobsSection
            settings={all.workers_jobs ?? {}}
            onSave={(s) => updateMut.mutate({ category: 'workers_jobs', settings: s })}
            isPending={updateMut.isPending}
            error={updateMut.error?.message}
          />
        </div>
      </div>
    </ErrorBoundary>
  )
}

function Section({
  title,
  desc,
  children,
}: {
  title: string
  desc: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-6">
      <h2 className="font-semibold text-slate-200 mb-1">{title}</h2>
      <p className="text-slate-500 text-sm mb-4">{desc}</p>
      {children}
    </section>
  )
}

function ModelsSection({
  settings,
  onSave,
  isPending,
  error,
}: {
  settings: Record<string, unknown>
  onSave: (s: Record<string, unknown>) => void
  isPending: boolean
  error?: string
}) {
  const [ollama_url, setOllama_url] = useState(str(settings.ollama_url))
  const [embed_model, setEmbed_model] = useState(str(settings.embed_model))
  const [ask_model, setAsk_model] = useState(str(settings.ask_model))

  useEffect(() => {
    setOllama_url(str(settings.ollama_url))
    setEmbed_model(str(settings.embed_model))
    setAsk_model(str(settings.ask_model))
  }, [settings.ollama_url, settings.embed_model, settings.ask_model])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({ ollama_url, embed_model, ask_model })
  }

  return (
    <Section title="Models" desc="Ollama URL and model names for embeddings and Ask.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-slate-400 text-sm mb-1">Ollama URL</label>
          <input
            type="url"
            value={ollama_url}
            onChange={(e) => setOllama_url(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
            placeholder="http://localhost:11434"
          />
        </div>
        <div>
          <label className="block text-slate-400 text-sm mb-1">Embedding model</label>
          <input
            type="text"
            value={embed_model}
            onChange={(e) => setEmbed_model(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
            placeholder="all-MiniLM-L6-v2"
          />
        </div>
        <div>
          <label className="block text-slate-400 text-sm mb-1">Ask (LLM) model</label>
          <input
            type="text"
            value={ask_model}
            onChange={(e) => setAsk_model(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
            placeholder="llama3.2"
          />
        </div>
        <SaveButton isPending={isPending} error={error} />
      </form>
    </Section>
  )
}

function InternetResearchSection({
  settings,
  onSave,
  isPending,
  error,
}: {
  settings: Record<string, unknown>
  onSave: (s: Record<string, unknown>) => void
  isPending: boolean
  error?: string
}) {
  const [enabled, setEnabled] = useState(bool(settings.enabled))

  useEffect(() => {
    setEnabled(bool(settings.enabled))
  }, [settings.enabled])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({ enabled })
  }

  return (
    <Section title="Internet Research" desc="When enabled, weak local results can trigger web search for external/current questions.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="rounded border-slate-600 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
          />
          <span className="text-slate-200">Enable web search for external questions</span>
        </label>
        <SaveButton isPending={isPending} error={error} />
      </form>
    </Section>
  )
}

function DocumentProcessingSection({
  settings,
  onSave,
  isPending,
  error,
}: {
  settings: Record<string, unknown>
  onSave: (s: Record<string, unknown>) => void
  isPending: boolean
  error?: string
}) {
  const [tika_endpoint, setTika_endpoint] = useState(str(settings.tika_endpoint))
  const [tika_timeout_secs, setTika_timeout_secs] = useState(num(settings.tika_timeout_secs).toString())

  useEffect(() => {
    setTika_endpoint(str(settings.tika_endpoint))
    setTika_timeout_secs(num(settings.tika_timeout_secs).toString())
  }, [settings.tika_endpoint, settings.tika_timeout_secs])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      tika_endpoint,
      tika_timeout_secs: parseFloat(tika_timeout_secs) || 60,
    })
  }

  return (
    <Section title="Document Processing" desc="Tika server endpoint for PDF/Office extraction.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-slate-400 text-sm mb-1">Tika endpoint</label>
          <input
            type="url"
            value={tika_endpoint}
            onChange={(e) => setTika_endpoint(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
            placeholder="http://localhost:9998"
          />
        </div>
        <div>
          <label className="block text-slate-400 text-sm mb-1">Tika timeout (seconds)</label>
          <input
            type="number"
            min={1}
            max={300}
            value={tika_timeout_secs}
            onChange={(e) => setTika_timeout_secs(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <SaveButton isPending={isPending} error={error} />
      </form>
    </Section>
  )
}

function ChatMemorySection({
  settings,
  onSave,
  isPending,
  error,
}: {
  settings: Record<string, unknown>
  onSave: (s: Record<string, unknown>) => void
  isPending: boolean
  error?: string
}) {
  const [retention_days, setRetention_days] = useState(num(settings.retention_days).toString())
  const [context_limit, setContext_limit] = useState(num(settings.context_limit).toString())

  useEffect(() => {
    setRetention_days(num(settings.retention_days).toString())
    setContext_limit(num(settings.context_limit).toString())
  }, [settings.retention_days, settings.context_limit])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      retention_days: parseInt(retention_days, 10) || 30,
      context_limit: parseInt(context_limit, 10) || 10,
    })
  }

  return (
    <Section title="Chat & Memory" desc="Conversation retention and context limits.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-slate-400 text-sm mb-1">Retention days</label>
          <input
            type="number"
            min={1}
            max={365}
            value={retention_days}
            onChange={(e) => setRetention_days(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-slate-400 text-sm mb-1">Context limit</label>
          <input
            type="number"
            min={1}
            max={100}
            value={context_limit}
            onChange={(e) => setContext_limit(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <SaveButton isPending={isPending} error={error} />
      </form>
    </Section>
  )
}

function WorkersJobsSection({
  settings,
  onSave,
  isPending,
  error,
}: {
  settings: Record<string, unknown>
  onSave: (s: Record<string, unknown>) => void
  isPending: boolean
  error?: string
}) {
  const [max_retries, setMax_retries] = useState(num(settings.max_retries).toString())
  const [retry_delay_secs, setRetry_delay_secs] = useState(num(settings.retry_delay_secs).toString())

  useEffect(() => {
    setMax_retries(num(settings.max_retries).toString())
    setRetry_delay_secs(num(settings.retry_delay_secs).toString())
  }, [settings.max_retries, settings.retry_delay_secs])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      max_retries: parseInt(max_retries, 10) || 3,
      retry_delay_secs: parseInt(retry_delay_secs, 10) || 60,
    })
  }

  return (
    <Section title="Workers & Jobs" desc="Job retry limits and delay.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-slate-400 text-sm mb-1">Max retries</label>
          <input
            type="number"
            min={0}
            max={20}
            value={max_retries}
            onChange={(e) => setMax_retries(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-slate-400 text-sm mb-1">Retry delay (seconds)</label>
          <input
            type="number"
            min={1}
            max={3600}
            value={retry_delay_secs}
            onChange={(e) => setRetry_delay_secs(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <SaveButton isPending={isPending} error={error} />
      </form>
    </Section>
  )
}

function SaveButton({ isPending, error }: { isPending: boolean; error?: string }) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="submit"
        disabled={isPending}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        {isPending ? 'Saving…' : 'Save'}
      </button>
      {error && <span className="text-red-400 text-sm">{error}</span>}
    </div>
  )
}
