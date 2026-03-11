import { describe, it, expect, beforeEach } from 'vitest'
import {
  createThread,
  getThreads,
  getThread,
  saveThread,
  updateThreadTitle,
  deleteThread,
} from '../chat'

describe('chat store', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('creates thread with id and title', () => {
    const t = createThread()
    expect(t.id).toMatch(/^t_/)
    expect(t.title).toBe('New chat')
    expect(t.messages).toEqual([])
    expect(t.createdAt).toBeLessThanOrEqual(Date.now())
  })

  it('saves and retrieves thread', () => {
    const t = createThread()
    t.messages = [{ role: 'user', content: 'Hi' }]
    saveThread(t)
    const loaded = getThread(t.id)
    expect(loaded?.id).toBe(t.id)
    expect(loaded?.messages).toHaveLength(1)
    expect(getThreads()).toHaveLength(1)
  })

  it('updates thread title', () => {
    const t = createThread()
    saveThread(t)
    updateThreadTitle(t.id, 'My chat')
    const loaded = getThread(t.id)
    expect(loaded?.title).toBe('My chat')
  })

  it('deletes thread', () => {
    const t = createThread()
    saveThread(t)
    expect(getThreads()).toHaveLength(1)
    deleteThread(t.id)
    expect(getThreads()).toHaveLength(0)
    expect(getThread(t.id)).toBeUndefined()
  })
})
