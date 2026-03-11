import { useState, useRef, useEffect, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Plus, MessageSquare, Sparkles, AlertCircle } from 'lucide-react'
import { ask } from '../lib/api'
import { CitationCard } from '../components/CitationCard'
import { WebCitationCard } from '../components/WebCitationCard'
import { ProvenanceDrawer } from '../components/ProvenanceDrawer'
import { LoadingDots } from '../components/Loading'
import { ErrorBoundary } from '../components/ErrorBoundary'
import {
  createThread,
  getThreads,
  getThread,
  saveThread,
  type ChatThread,
  type ChatMessage,
} from '../store/chat'

const STARTER_PROMPTS = [
  'What are the key points in my documents?',
  'Summarize the main findings',
  'Find documents about a specific topic',
  'Compare different sources',
]

/** Pending assistant message marker */
const PENDING_ID = '__pending__'

export function AskPage() {
  const [threads, setThreads] = useState<ChatThread[]>(() => getThreads())
  const [activeId, setActiveId] = useState<string | null>(() => {
    const t = getThreads()
    return t[0]?.id ?? null
  })
  const [question, setQuestion] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const activeThread = activeId ? getThread(activeId) : null
  const messages = activeThread?.messages ?? []

  const persist = useCallback((thread: ChatThread) => {
    saveThread(thread)
    setThreads(getThreads())
  }, [])

  const askMut = useMutation({
    mutationFn: async (payload: { question: string; threadId: string }) => {
      const res = await ask(payload.question)
      return { ...res, _threadId: payload.threadId, _question: payload.question }
    },
    onSuccess: (data) => {
      const t = getThread(data._threadId)
      if (!t) return
      const withoutPending = t.messages.filter((m) => (m as ChatMessage & { chunk_id?: string }).chunk_id !== PENDING_ID)
      const sourceType = data.answer_source_type ?? data.source_type ?? 'local'
      const next: ChatMessage[] = [
        ...withoutPending,
        {
          role: 'assistant',
          content: data.answer || 'No answer returned.',
          citations: data.local_citations ?? data.citations ?? [],
          webCitations: data.web_citations ?? [],
          sourceType,
          answerSourceType: sourceType,
        },
      ]
      const title = t.messages.length <= 1 ? (data._question.slice(0, 40) + (data._question.length > 40 ? '…' : '')) : t.title
      persist({ ...t, messages: next, title })
    },
    onError: (err: Error, payload) => {
      const t = getThread(payload.threadId)
      if (!t) return
      const withoutPending = t.messages.filter((m) => (m as ChatMessage & { chunk_id?: string }).chunk_id !== PENDING_ID)
      const next: ChatMessage[] = [
        ...withoutPending,
        {
          role: 'assistant',
          content: `Error: ${err.message}\n\nCheck that the control API (port 3000) and query API (port 3001) are running, and that you have workspace access.`,
          citations: [],
        } as ChatMessage & { chunk_id?: string },
      ]
      const title = t.messages.length <= 1 ? (payload.question.slice(0, 40) + (payload.question.length > 40 ? '…' : '')) : t.title
      persist({ ...t, messages: next, title })
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, askMut.isPending])

  const handleNewChat = () => {
    const t = createThread()
    persist(t)
    setActiveId(t.id)
    setQuestion('')
  }

  const handleSelectThread = (id: string) => {
    setActiveId(id)
    setQuestion('')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = question.trim()
    if (!q || askMut.isPending) return

    let threadId = activeId
    if (!threadId) {
      const t = createThread()
      persist(t)
      setActiveId(t.id)
      threadId = t.id
    }

    const t = getThread(threadId)
    if (!t) return

    const userMsg: ChatMessage = { role: 'user', content: q }
    const pendingMsg = { role: 'assistant' as const, content: '', citations: [], chunk_id: PENDING_ID } as ChatMessage & { chunk_id?: string }
    const next: ChatMessage[] = [...t.messages, userMsg, pendingMsg]
    const title = t.messages.length === 0 ? (q.slice(0, 40) + (q.length > 40 ? '…' : '')) : t.title
    persist({ ...t, messages: next, title })

    setQuestion('')
    askMut.mutate({ question: q, threadId })
  }

  const [provenanceId, setProvenanceId] = useState<string | null>(null)
  const lastCitations = messages.filter((m) => m.role === 'assistant').pop()?.citations ?? []
  const citationForProvenance = lastCitations.find((c) => c.source_item_id === provenanceId)

  return (
    <ErrorBoundary>
      <div className="flex h-[calc(100vh-6rem)] gap-4">
        <aside className="w-64 shrink-0 flex flex-col rounded-xl border border-slate-800/80 bg-slate-900/40 overflow-hidden">
          <div className="p-3 border-b border-slate-800/80">
            <button
              onClick={handleNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              New chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {threads.length === 0 ? (
              <p className="text-slate-500 text-sm px-2 py-4">No chats yet</p>
            ) : (
              <ul className="space-y-1">
                {threads.map((t) => (
                  <li key={t.id}>
                    <button
                      onClick={() => handleSelectThread(t.id)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors truncate ${
                        activeId === t.id
                          ? 'bg-slate-700/80 text-white'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                      }`}
                    >
                      <MessageSquare className="w-4 h-4 inline-block mr-2 opacity-70" />
                      {t.title || 'New chat'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>

        <main className="flex-1 flex flex-col min-w-0 rounded-xl border border-slate-800/80 bg-slate-900/40 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="p-4 rounded-full bg-slate-800/80 mb-4">
                  <Sparkles className="w-10 h-10 text-sky-400" />
                </div>
                <h2 className="text-lg font-semibold text-slate-200 mb-2">Ask your knowledge base</h2>
                <p className="text-slate-500 text-sm max-w-md mb-4">
                  Get answers grounded in your documents. Citations link back to source material.
                </p>
                <p className="text-slate-600 text-xs max-w-md mb-6 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <strong>Local + optional web.</strong> Answers use your documents first. When local content is insufficient and web research is enabled, external sources may be used. Source type (Local / Web / Mixed) is shown with each answer. When disabled, Questions outside your indexed documents will return “no relevant content found.”
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                  {STARTER_PROMPTS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setQuestion(p)}
                      className="text-left px-4 py-3 rounded-lg border border-slate-700/60 bg-slate-800/40 text-slate-300 hover:border-slate-600 hover:bg-slate-800/70 text-sm transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => {
              const isPending = (m as ChatMessage & { chunk_id?: string }).chunk_id === PENDING_ID
              const isError = m.role === 'assistant' && m.content?.startsWith('Error:')
              return (
                <div
                  key={i}
                  className={`flex gap-4 mb-6 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-xl px-4 py-3 ${
                      m.role === 'user'
                        ? 'bg-sky-600/80 text-white'
                        : isError
                          ? 'bg-red-900/30 border border-red-800/50 text-red-200'
                          : 'bg-slate-800/60 text-slate-200'
                    }`}
                  >
                    {isPending ? (
                      <div className="flex items-center gap-2 text-slate-400">
                        <LoadingDots />
                        <span className="text-sm">Finding relevant content…</span>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    )}
                    {m.role === 'assistant' && !isPending && (m.citations?.length || m.webCitations?.length) ? (
                      <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-4">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Sources</span>
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${
                              m.answerSourceType === 'local'
                                ? 'bg-sky-900/50 text-sky-300'
                                : m.answerSourceType === 'web'
                                  ? 'bg-amber-900/50 text-amber-300'
                                  : m.answerSourceType === 'mixed'
                                    ? 'bg-violet-900/50 text-violet-300'
                                    : 'bg-slate-700/50 text-slate-400'
                            }`}
                          >
                            {m.answerSourceType === 'local' ? 'Local' : m.answerSourceType === 'web' ? 'Web' : m.answerSourceType === 'mixed' ? 'Mixed' : m.sourceType || 'Local'}
                          </span>
                        </div>
                        {m.citations && m.citations.length > 0 && (
                          <div>
                            <p className="text-xs text-slate-500 mb-2">Documents</p>
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
                        {m.webCitations && m.webCitations.length > 0 && (
                          <div>
                            <p className="text-xs text-slate-500 mb-2">Web</p>
                            <div className="flex flex-wrap gap-2">
                              {m.webCitations.map((c, i) => (
                                <WebCitationCard key={`${c.url}-${i}`} citation={c} />
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              )
            })}
            <div ref={bottomRef} />
          </div>
          <div className="p-4 border-t border-slate-800/80">
            <p className="text-xs text-slate-500 mb-3">
              Local documents first. Enable web search for external questions in Settings → Internet Research.
            </p>
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question…"
                disabled={askMut.isPending}
                className="flex-1 px-4 py-3 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent disabled:opacity-50"
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
        </main>
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
