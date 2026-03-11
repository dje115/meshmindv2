/**
 * Chat/Ask UX store: conversations and threads.
 * Session-backed for now (memory/retention controls planned later).
 */

import type { Citation, WebCitation } from '../lib/api'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  webCitations?: WebCitation[]
  sourceType?: string
  answerSourceType?: 'local' | 'web' | 'mixed'
}

export interface ChatThread {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

const STORAGE_KEY = 'meshmind_chat_threads'
const MAX_THREADS = 50

function loadThreads(): ChatThread[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as ChatThread[]
    return Array.isArray(parsed) ? parsed.slice(0, MAX_THREADS) : []
  } catch {
    return []
  }
}

function saveThreads(threads: ChatThread[]) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(threads.slice(0, MAX_THREADS)))
  } catch {
    // ignore
  }
}

function generateId(): string {
  return `t_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

export function createThread(): ChatThread {
  return {
    id: generateId(),
    title: 'New chat',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
}

export function getThreads(): ChatThread[] {
  return loadThreads()
}

export function getThread(id: string): ChatThread | undefined {
  return loadThreads().find((t) => t.id === id)
}

export function saveThread(thread: ChatThread): void {
  const threads = loadThreads()
  const idx = threads.findIndex((t) => t.id === thread.id)
  if (idx >= 0) {
    threads[idx] = { ...thread, updatedAt: Date.now() }
  } else {
    threads.unshift({ ...thread, updatedAt: Date.now() })
  }
  saveThreads(threads)
}

export function updateThreadTitle(id: string, title: string): void {
  const threads = loadThreads()
  const t = threads.find((x) => x.id === id)
  if (t) {
    t.title = title
    t.updatedAt = Date.now()
    saveThreads(threads)
  }
}

export function deleteThread(id: string): void {
  const threads = loadThreads().filter((t) => t.id !== id)
  saveThreads(threads)
}
