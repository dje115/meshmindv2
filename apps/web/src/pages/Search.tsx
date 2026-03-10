import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search as SearchIcon } from 'lucide-react'
import { search } from '../lib/api'
import { CitationCard } from '../components/CitationCard'
import { ProvenanceDrawer } from '../components/ProvenanceDrawer'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function SearchPage() {
  const [q, setQ] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [provenanceId, setProvenanceId] = useState<string | null>(null)

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['search', submitted],
    queryFn: () => search(submitted, 20),
    enabled: submitted.length > 0,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitted(q.trim())
  }

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Search</h1>
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="relative">
            <SearchIcon
              className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500"
              aria-hidden
            />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search your knowledge base…"
              className="w-full pl-12 pr-4 py-3 rounded-lg bg-slate-800/50 border border-slate-600 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              aria-label="Search query"
            />
          </div>
          <button
            type="submit"
            disabled={!q.trim() || isLoading}
            className="mt-3 px-4 py-2 rounded-md bg-sky-600 hover:bg-sky-500 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Search
          </button>
        </form>
        {submitted && (
          <>
            {isFetching ? (
              <p className="text-slate-500">Searching…</p>
            ) : data ? (
              <section>
                <p className="text-sm text-slate-500 mb-4">
                  {data.total} result{data.total !== 1 ? 's' : ''}
                </p>
                <div className="space-y-4">
                  {data.chunks.map((chunk) => (
                    <div
                      key={`${chunk.chunk_id}-${chunk.rank}`}
                      className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4"
                    >
                      <CitationCard
                        citation={chunk}
                        onOpenProvenance={setProvenanceId}
                      />
                      <p className="mt-3 text-slate-300 text-sm whitespace-pre-wrap line-clamp-4">
                        {chunk.text}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <span className="text-xs text-slate-500">
                          {chunk.match_type}
                        </span>
                        <span className="text-xs text-slate-500">
                          score: {chunk.score.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ) : (
              <p className="text-slate-500">No results.</p>
            )}
          </>
        )}
      </div>
      <ProvenanceDrawer
        sourceItemId={provenanceId}
        onClose={() => setProvenanceId(null)}
        filename={data?.chunks.find((c) => c.source_item_id === provenanceId)?.filename}
        pageIndex={data?.chunks.find((c) => c.source_item_id === provenanceId)?.page_index}
        sheetName={data?.chunks.find((c) => c.source_item_id === provenanceId)?.sheet_name}
      />
    </ErrorBoundary>
  )
}
