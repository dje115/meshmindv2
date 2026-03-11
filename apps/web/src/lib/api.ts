/**
 * MeshMind v2 API client.
 * Uses relative paths; Vite proxies /api to control-api.
 */

const API = '/api'

function headers(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const h: HeadersInit = { 'Content-Type': 'application/json' }
  if (token) (h as Record<string, string>)['Authorization'] = `Bearer ${token}`
  return h
}

async function handleResp<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    const msg = err?.error?.message ?? err?.detail ?? (typeof err?.detail === 'string' ? err.detail : r.statusText)
    const detail = Array.isArray(err?.detail)
      ? err.detail.map((d: { loc?: unknown[]; msg?: string }) => `${d.loc?.join('.') ?? 'body'}: ${d.msg ?? ''}`).join('; ')
      : null
    throw new Error(detail || (typeof msg === 'string' ? msg : r.statusText))
  }
  if (r.status === 204) return undefined as T
  return r.json()
}

// Auth
export async function login(username: string, password: string) {
  const r = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await handleResp<{ token: string; user: { id: string; username: string } }>(r)
  return data
}

export async function me() {
  const r = await fetch(`${API}/me`, { headers: headers() })
  return handleResp<{ id: string; username: string; email?: string }>(r)
}

// Workspaces
export async function workspacesList() {
  const r = await fetch(`${API}/workspaces`, { headers: headers() })
  return handleResp<Workspace[]>(r)
}

// Sources
export async function sourcesList(workspaceId?: string) {
  const q = workspaceId ? `?workspace_id=${workspaceId}` : ''
  const r = await fetch(`${API}/sources${q}`, { headers: headers() })
  return handleResp<Source[]>(r)
}

export interface CreateSourceRequest {
  workspace_id: string
  name: string
  kind: 'filesystem' | 'sqlite' | 'csv' | 'json'
  config?: {
    path?: string
    root_path?: string
    include_patterns?: string[]
    exclude_patterns?: string[]
    max_depth?: number
    enabled?: boolean
  }
}

export async function sourceCreate(req: CreateSourceRequest) {
  const r = await fetch(`${API}/sources`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(req),
  })
  return handleResp<Source>(r)
}

export interface UpdateSourceRequest {
  name?: string
  kind?: 'filesystem' | 'sqlite' | 'csv' | 'json'
  config?: Record<string, unknown>
  status?: string
}

export async function sourceUpdate(id: string, req: UpdateSourceRequest) {
  const r = await fetch(`${API}/sources/${id}`, {
    method: 'PUT',
    headers: headers(),
    body: JSON.stringify(req),
  })
  return handleResp<Source>(r)
}

export async function sourceIngest(id: string) {
  const r = await fetch(`${API}/sources/${id}/ingest`, {
    method: 'POST',
    headers: headers(),
  })
  return handleResp<Job>(r)
}

// Agents
export async function agentsList(status?: string) {
  const q = status ? `?status=${status}` : ''
  const r = await fetch(`${API}/agents${q}`, { headers: headers() })
  return handleResp<Agent[]>(r)
}

// Jobs
export async function jobsList(sourceId?: string, status?: string, limit = 20) {
  const params = new URLSearchParams()
  if (sourceId) params.set('source_id', sourceId)
  if (status) params.set('status', status)
  params.set('limit', String(limit))
  const r = await fetch(`${API}/jobs?${params}`, { headers: headers() })
  return handleResp<Job[]>(r)
}

// Search
export async function search(q: string, limit = 20, sourceIds?: string) {
  const params = new URLSearchParams({ q, limit: String(limit) })
  if (sourceIds) params.set('source_ids', sourceIds)
  const r = await fetch(`${API}/search?${params}`, { headers: headers() })
  return handleResp<SearchResponse>(r)
}

// Documents
export async function documentDetail(id: string) {
  const r = await fetch(`${API}/documents/${id}`, { headers: headers() })
  return handleResp<DocumentDetail>(r)
}

export async function documentProvenance(id: string) {
  const r = await fetch(`${API}/documents/${id}/provenance`, { headers: headers() })
  return handleResp<ProvenanceDetail>(r)
}

// Ask
export async function ask(question: string, workspaceIds?: string[], sourceIds?: string[], maxChunks = 10) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000) // 2 min
  try {
    const r = await fetch(`${API}/ask`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ question, workspace_ids: workspaceIds, source_ids: sourceIds, max_chunks: maxChunks }),
      signal: controller.signal,
    })
    return handleResp<AskResponse>(r)
  } catch (e) {
    if (e instanceof Error && e.name === 'AbortError') {
      throw new Error('Request timed out after 2 minutes. Ensure query-api (port 3001), Ollama, and Qdrant are running.')
    }
    throw e
  } finally {
    clearTimeout(timeout)
  }
}

// Components status
export interface ComponentStatus {
  status: string
  message?: string
}

export interface ComponentsStatusResponse {
  control_api: ComponentStatus
  database: ComponentStatus
  query_api: ComponentStatus
  ollama: ComponentStatus
  qdrant: ComponentStatus
}

export async function componentsStatus(): Promise<ComponentsStatusResponse> {
  const r = await fetch(`${API}/components/status`, { headers: headers() })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    const msg = err?.error?.message ?? err?.detail ?? r.statusText
    throw new Error(typeof msg === 'string' ? msg : `HTTP ${r.status}`)
  }
  return r.json()
}

// Settings (admin)
export type AppSettings = Record<string, Record<string, unknown>>

export async function settingsGet(): Promise<AppSettings> {
  const r = await fetch(`${API}/settings`, { headers: headers() })
  return handleResp<AppSettings>(r)
}

export async function settingsUpdate(category: string, settings: Record<string, unknown>): Promise<Record<string, unknown>> {
  const r = await fetch(`${API}/settings`, {
    method: 'PUT',
    headers: headers(),
    body: JSON.stringify({ category, settings }),
  })
  return handleResp<Record<string, unknown>>(r)
}

// Roles, Users (admin)
export async function rolesList() {
  const r = await fetch(`${API}/roles`, { headers: headers() })
  return handleResp<Role[]>(r)
}

export async function usersList() {
  const r = await fetch(`${API}/users`, { headers: headers() })
  return handleResp<User[]>(r)
}

// Types
export interface Workspace {
  id: string
  name: string
  slug: string
  description?: string
}

export interface Source {
  id: string
  workspace_id: string
  name: string
  kind: string
  config: Record<string, unknown>
  status: string
}

export interface Agent {
  id: string
  name: string
  capabilities: string[]
  status: string
  last_heartbeat: string
}

export interface Job {
  id: string
  source_id: string
  source_item_id?: string
  agent_id?: string
  job_kind?: string
  status: string
  claimed_at?: string
  completed_at?: string
  error?: string
  created_at: string
}

export interface SearchChunk {
  chunk_id: string
  source_item_id: string
  source_id: string
  workspace_id: string
  text: string
  page_index?: number
  sheet_index?: number
  sheet_name?: string
  score: number
  rank: number
  match_type: string
  filename?: string
  open_target?: string
}

export interface SearchResponse {
  chunks: SearchChunk[]
  facets: Record<string, { value: string; count: number }[]>
  total: number
}

export interface DocumentDetail {
  id: string
  source_id: string
  workspace_id: string
  fingerprint: string
  provenance: Record<string, unknown>
  chunks: Array<{ text?: string; chunk_id?: string; page_index?: number }>
}

export interface ProvenanceDetail {
  source_item_id: string
  source_id: string
  workspace_id: string
  provenance: Record<string, unknown>
  absolute_path?: string
  filename?: string
  open_target?: string
}

export interface Citation {
  chunk_id: string
  source_item_id: string
  text: string
  page_index?: number
  sheet_index?: number
  sheet_name?: string
  score?: number
  filename?: string
  open_target?: string
}

export interface WebCitation {
  title: string
  source: string
  url: string
  snippet: string
}

export interface AskResponse {
  answer: string
  citations: Citation[]
  local_citations?: Citation[]
  web_citations?: WebCitation[]
  answer_source_type?: 'local' | 'web' | 'mixed'
  source_type: 'local' | 'web' | 'mixed'
  confidence?: number
  coverage?: number
  related_documents: string[]
  grounded: boolean
}

export interface Role {
  id: string
  name: string
  description?: string
}

export interface User {
  id: string
  username: string
  email?: string
  display_name?: string
}
