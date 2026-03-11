import { ExternalLink } from 'lucide-react'
import type { WebCitation } from '../lib/api'

interface WebCitationCardProps {
  citation: WebCitation
}

export function WebCitationCard({ citation }: WebCitationCardProps) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-3">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium text-slate-200">{citation.title || citation.source}</span>
            {citation.source && (
              <span className="text-slate-500 text-xs">{citation.source}</span>
            )}
          </div>
          {citation.snippet && (
            <p className="mt-1.5 text-slate-400 text-sm line-clamp-2">{citation.snippet}</p>
          )}
          {citation.url && (
            <a
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300"
            >
              <ExternalLink className="w-3 h-3" aria-hidden />
              Open
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
