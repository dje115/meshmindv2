import { FileText, ExternalLink } from 'lucide-react'
import type { Citation, SearchChunk } from '../lib/api'

interface CitationCardProps {
  citation: Citation | SearchChunk
  onOpenProvenance?: (sourceItemId: string) => void
  compact?: boolean
}

export function CitationCard({ citation, onOpenProvenance, compact }: CitationCardProps) {
  const filename = citation.filename ?? 'Document'
  const pageRef =
    citation.page_index != null
      ? `Page ${citation.page_index + 1}`
      : citation.sheet_name
        ? `Sheet: ${citation.sheet_name}`
        : null
  const openTarget = citation.open_target
  const text = citation.text

  return (
    <div
      className={`rounded-lg border border-slate-700/50 bg-slate-800/30 ${
        compact ? 'p-3' : 'p-4'
      }`}
    >
      <div className="flex items-start gap-3">
        <FileText className="w-4 h-4 shrink-0 text-slate-500 mt-0.5" aria-hidden />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium text-slate-200">{filename}</span>
            {pageRef && (
              <span className="text-slate-500">{pageRef}</span>
            )}
          </div>
          {!compact && text && (
            <p className="mt-2 text-slate-400 text-sm line-clamp-2">{text}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-2">
            {onOpenProvenance && (
              <button
                onClick={() => onOpenProvenance(citation.source_item_id)}
                className="text-xs text-sky-400 hover:text-sky-300"
              >
                View provenance
              </button>
            )}
            {openTarget && (
              <a
                href={openTarget}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300"
              >
                <ExternalLink className="w-3 h-3" aria-hidden />
                Open original
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
