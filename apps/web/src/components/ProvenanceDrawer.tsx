import { useState, useEffect } from 'react'
import { X, ExternalLink } from 'lucide-react'
import { documentProvenance, type ProvenanceDetail } from '../lib/api'

interface ProvenanceDrawerProps {
  sourceItemId: string | null
  onClose: () => void
  filename?: string
  pageIndex?: number
  sheetName?: string
}

export function ProvenanceDrawer({
  sourceItemId,
  onClose,
  filename,
  pageIndex,
  sheetName,
}: ProvenanceDrawerProps) {
  const [provenance, setProvenance] = useState<ProvenanceDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!sourceItemId) {
      setProvenance(null)
      return
    }
    setLoading(true)
    documentProvenance(sourceItemId)
      .then(setProvenance)
      .catch(() => setProvenance(null))
      .finally(() => setLoading(false))
  }, [sourceItemId])

  if (!sourceItemId) return null

  const displayName = filename ?? provenance?.filename ?? 'Document'
  const pageRef = pageIndex != null ? `Page ${pageIndex + 1}` : sheetName ?? null
  const openTarget = provenance?.open_target

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden
      />
      <aside
        className="fixed right-0 top-0 h-full w-full max-w-md bg-slate-900 border-l border-slate-700 shadow-xl z-50 flex flex-col"
        role="dialog"
        aria-labelledby="provenance-title"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
          <h2 id="provenance-title" className="font-semibold text-slate-100">
            Provenance
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <p className="text-slate-500">Loading…</p>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                  Document
                </p>
                <p className="text-slate-200">{displayName}</p>
              </div>
              {pageRef && (
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                    Reference
                  </p>
                  <p className="text-slate-200">{pageRef}</p>
                </div>
              )}
              {provenance?.absolute_path && (
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                    Path
                  </p>
                  <p className="text-slate-400 text-sm font-mono break-all">
                    {provenance.absolute_path}
                  </p>
                </div>
              )}
              {openTarget && (
                <a
                  href={openTarget}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-slate-800 text-sky-400 hover:bg-slate-700 hover:text-sky-300 text-sm transition-colors"
                >
                  <ExternalLink className="w-4 h-4" aria-hidden />
                  Open original file
                </a>
              )}
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                  Source item ID
                </p>
                <p className="text-slate-500 text-xs font-mono">{sourceItemId}</p>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
