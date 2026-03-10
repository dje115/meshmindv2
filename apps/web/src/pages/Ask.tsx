import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, FileText } from 'lucide-react'
import { ask, type Citation } from '../lib/api'
import { CitationCard } from '../components/CitationCard'
import { ProvenanceDrawer } from '../components/ProvenanceDrawer'
import { LoadingDots } from '../components/Loading'
import { ErrorBoundary } from '../components/ErrorBoundary'

export function AskPage() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; citations?: Citation[]; sourceType?: string }>>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  const askMut = useMutation({
    mutationFn: (q: string) => ask(q),
    onSuccess: (data, q) => {
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: q },
        {
          role: 'assistant',
          content: data.answer,
          citations: data.citations,
          sourceType: data.source_type,
        },
      ])
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const [provenanceId, setProvenanceId] = useState<string | null>(null)
  const lastCitations = messages.filter((m) => m.role === 'assistant').pop()?.citations ?? []
  const citationForProvenance = lastCitations.find((c) => c.source_item_id === provenanceId)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = question.trim()
    if (!q || askMut.isPending) return
    setQuestion('')
    askMut.mutate(q)
  }

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
        <h1 className="text-2xl font-bold text-slate-100 mb-4">Ask</h1>
        <p className="text-slate-500 text-sm mb-6">
          Ask questions about your documents. Answers are grounded in your knowledge base with citations.
        </p>
        <div className="flex-1 overflow-y-auto space-y-6 mb-4">
          {messages.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-600 p-12 text-center text-slate-500">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" aria-hidden />
              <p>Ask a question to get started.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`rounded-lg p-4 ${
                m.role === 'user' ? 'bg-slate-800/50 ml-0 mr-8' : 'bg-slate-800/30 mr-0 ml-8'
              }`}
            >
              <p className="text-slate-300 whitespace-pre-wrap">{m.content}</p>
              {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-700/50">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                    Sources
                    {m.sourceType === 'local' && (
                      <span className="ml-2 text-sky-400">(local knowledge)</span>
                    )}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {m.citations.map((c) => (
                      <CitationCard
                        key={c.chunk_id}
                        citation={c}
                        onOpenProvenance={setProvenanceId}
                        compact
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {askMut.isPending && (
            <div className="rounded-lg p-4 bg-slate-800/30 ml-8">
              <LoadingDots />
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question…"
            disabled={askMut.isPending}
            className="flex-1 px-4 py-3 rounded-lg bg-slate-800/50 border border-slate-600 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent disabled:opacity-50"
            aria-label="Question"
          />
          <button
            type="submit"
            disabled={!question.trim() || askMut.isPending}
            className="p-3 rounded-lg bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Send"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
      <ProvenanceDrawer
        sourceItemId={provenanceId}
        onClose={() => setProvenanceId(null)}
        filename={citationForProvenance?.filename}
        pageIndex={citationForProvenance?.page_index}
        sheetName={citationForProvenance?.sheet_name}
      />
    </ErrorBoundary>
  )
}
