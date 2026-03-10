import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { documentDetail, type DocumentDetail } from '../lib/api'

interface DocumentPreviewPanelProps {
  sourceItemId: string | null
  onClose: () => void
}

export function DocumentPreviewPanel({ sourceItemId, onClose }: DocumentPreviewPanelProps) {
  const [doc, setDoc] = useState<DocumentDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!sourceItemId) {
      setDoc(null)
      return
    }
    setLoading(true)
    documentDetail(sourceItemId)
      .then(setDoc)
      .catch(() => setDoc(null))
      .finally(() => setLoading(false))
  }, [sourceItemId])

  if (!sourceItemId) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden
      />
      <aside
        className="fixed right-0 top-0 h-full w-full max-w-2xl bg-slate-900 border-l border-slate-700 shadow-xl z-50 flex flex-col"
        role="dialog"
        aria-labelledby="doc-preview-title"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
          <h2 id="doc-preview-title" className="font-semibold text-slate-100">
            Document Preview
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
          ) : doc ? (
            <div className="space-y-4">
              {doc.chunks?.map((c, i) => (
                <div
                  key={c.chunk_id ?? i}
                  className="rounded-lg border border-slate-700/50 p-4 bg-slate-800/30"
                >
                  {c.page_index != null && (
                    <p className="text-xs text-slate-500 mb-2">Page {c.page_index + 1}</p>
                  )}
                  <p className="text-slate-300 text-sm whitespace-pre-wrap">{c.text ?? ''}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500">Document not found.</p>
          )}
        </div>
      </aside>
    </>
  )
}
