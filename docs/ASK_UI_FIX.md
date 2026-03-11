# Ask UI Fix – Diagnosis and Summary

## What Was Broken

1. **User message never appeared**
   - The user message was only added in `onSuccess`, so it appeared only after the API responded.
   - If the API failed or took a long time, the user saw nothing.

2. **`activeId` race when creating a new thread**
   - When there was no active thread, `handleSubmit` created one and called `setActiveId(t.id)`.
   - React state updates are async; `onSuccess` captured the previous `activeId` (null).
   - `onSuccess` returned early due to `if (!activeId) return`, so the assistant reply was never stored.
   - Result: user message and assistant reply both missing for new chats.

3. **No error handling**
   - `useMutation` had no `onError`, so API/network errors were not shown.
   - Failures were silent.

4. **No explicit loading or no-result states**
   - Loading used `askMut.isPending`, but the user message wasn’t visible yet.
   - No clear “Finding relevant content…” state.
   - Backend already returns “no relevant content” and model-unavailable messages, but the UI didn’t surface them clearly.

5. **Unclear local-only scope**
   - Users were not told that only local knowledge is supported or that web research is not implemented.

## Fixes Applied

1. **Optimistic user message** – Add the user message to the thread immediately on submit, before calling the API.

2. **Mutation variables** – Pass `{ question, threadId }` to `mutate()` so `onSuccess` and `onError` use `threadId` from the payload instead of closure `activeId`.

3. **Pending assistant message** – Add a placeholder assistant message when submitting, show “Finding relevant content…”, and replace it with the real response or error.

4. **Error handling** – `onError` stores an error message in the thread and shows it in a distinct error style.

5. **Local-only messaging** – Empty state and input area state that only local knowledge is used and that web research will be added later.

## Web Research Status

**Web research is not implemented.**  
The query API only uses local documents (chunk index + Qdrant). All answers come from hybrid search over indexed chunks. For questions outside that scope, the backend returns:

> "I couldn't find relevant content in your documents. Please try a different question or ensure documents are indexed."

To add controlled web research later you would need:

1. A policy/flag for when to use web search (e.g. workspace setting, per-query toggle).
2. A search provider integration (e.g. Bing, Serper).
3. Changes to the ask flow to optionally call web search and merge results.
4. Clear labeling of answers as “local”, “web”, or “combined”.
