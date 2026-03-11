import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { sourceCreate, workspacesList, type CreateSourceRequest } from '../lib/api'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function AddSourcePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [workspaceId, setWorkspaceId] = useState('')
  const [path, setPath] = useState('')
  const [includePatterns, setIncludePatterns] = useState('')
  const [excludePatterns, setExcludePatterns] = useState('**/node_modules/**\n**/.git/**')
  const [enabled, setEnabled] = useState(true)

  const createMut = useMutation({
    mutationFn: (req: CreateSourceRequest) => sourceCreate(req),
    onSuccess: (source) => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      navigate(`/sources/${source.id}`)
    },
  })

  const { data: workspacesData = [] } = useQuery({
    queryKey: ['workspaces'],
    queryFn: workspacesList,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!workspaceId || !name.trim()) return
    const include = includePatterns
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    const exclude = excludePatterns
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    createMut.mutate({
      workspace_id: workspaceId,
      name: name.trim(),
      kind: 'filesystem',
      config: {
        path: path.trim() || undefined,
        include_patterns: include.length ? include : undefined,
        exclude_patterns: exclude.length ? exclude : undefined,
        enabled,
      },
    })
  }

  return (
    <ErrorBoundary>
      <div className="max-w-2xl">
        <button
          onClick={() => navigate('/sources')}
          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Sources
        </button>
        <h1 className="text-2xl font-bold text-slate-100 mb-2">Add source</h1>
        <p className="text-slate-500 text-sm mb-8">
          Connect a filesystem path to scan documents. Supported: PDF, DOCX, XLSX, TXT, MD, images.
        </p>
        <AddSourceForm
          name={name}
          setName={setName}
          workspaceId={workspaceId}
          setWorkspaceId={setWorkspaceId}
          path={path}
          setPath={setPath}
          includePatterns={includePatterns}
          setIncludePatterns={setIncludePatterns}
          excludePatterns={excludePatterns}
          setExcludePatterns={setExcludePatterns}
          enabled={enabled}
          setEnabled={setEnabled}
          workspaces={workspacesData}
          navigate={navigate}
          onSubmit={handleSubmit}
          isPending={createMut.isPending}
          error={createMut.error?.message}
        />
      </div>
    </ErrorBoundary>
  )
}

// Split form to avoid hooks in wrong order
function AddSourceForm({
  name,
  setName,
  workspaceId,
  setWorkspaceId,
  path,
  setPath,
  includePatterns,
  setIncludePatterns,
  excludePatterns,
  setExcludePatterns,
  enabled,
  setEnabled,
  workspaces,
  navigate,
  onSubmit,
  isPending,
  error,
}: {
  name: string
  setName: (s: string) => void
  workspaceId: string
  setWorkspaceId: (s: string) => void
  path: string
  setPath: (s: string) => void
  includePatterns: string
  setIncludePatterns: (s: string) => void
  excludePatterns: string
  setExcludePatterns: (s: string) => void
  enabled: boolean
  setEnabled: (b: boolean) => void
  workspaces: { id: string; name: string }[]
  navigate: (path: string) => void
  onSubmit: (e: React.FormEvent) => void
  isPending: boolean
  error?: string
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {error && (
        <div className="p-4 rounded-lg bg-red-900/30 border border-red-800/50 text-red-300 text-sm">
          {error}
        </div>
      )}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
          Source name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Company Docs"
          required
          className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
        />
      </div>
      <div>
        <label htmlFor="workspace" className="block text-sm font-medium text-slate-300 mb-2">
          Workspace
        </label>
        <select
          id="workspace"
          value={workspaceId}
          onChange={(e) => setWorkspaceId(e.target.value)}
          required
          className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          <option value="">Select workspace</option>
          {workspaces.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="path" className="block text-sm font-medium text-slate-300 mb-2">
          Path
        </label>
        <input
          id="path"
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="e.g. C:\Documents or /home/user/docs"
          className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent font-mono text-sm"
        />
        <p className="mt-1.5 text-xs text-slate-500">Absolute path to the root folder to scan.</p>
      </div>
      <div>
        <label htmlFor="include" className="block text-sm font-medium text-slate-300 mb-2">
          Include patterns (optional)
        </label>
        <textarea
          id="include"
          value={includePatterns}
          onChange={(e) => setIncludePatterns(e.target.value)}
          placeholder="**/*.pdf&#10;**/*.docx"
          rows={2}
          className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono text-sm resize-none"
        />
        <p className="mt-1.5 text-xs text-slate-500">Glob patterns, one per line. Leave empty for all supported types.</p>
      </div>
      <div>
        <label htmlFor="exclude" className="block text-sm font-medium text-slate-300 mb-2">
          Exclude patterns
        </label>
        <textarea
          id="exclude"
          value={excludePatterns}
          onChange={(e) => setExcludePatterns(e.target.value)}
          rows={3}
          className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono text-sm resize-none"
        />
        <p className="mt-1.5 text-xs text-slate-500">Glob patterns to skip (e.g. node_modules, .git).</p>
      </div>
      <div className="flex items-center gap-2">
        <input
          id="enabled"
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="rounded border-slate-600 bg-slate-800 text-sky-500 focus:ring-sky-500"
        />
        <label htmlFor="enabled" className="text-sm text-slate-400">
          Enabled (ready for ingest)
        </label>
      </div>
      <div className="flex flex-wrap gap-3 pt-4 border-t border-slate-800">
        <button
          type="submit"
          disabled={isPending}
          className="px-5 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          className="px-5 py-2.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium transition-colors"
          onClick={() => navigate('/sources')}
        >
          Cancel
        </button>
        <div className="flex-1" />
        <p className="text-xs text-slate-500 self-center">
          Ingest: triggered via workers when configured. Backend ingest API coming.
        </p>
      </div>
    </form>
  )
}
