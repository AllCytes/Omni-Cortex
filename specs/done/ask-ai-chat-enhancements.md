# Ask AI Chat Enhancements Implementation Plan

## Overview

Enhance the OmniCortex Dashboard "Ask AI" chat feature to match modern AI chat UX standards from ChatGPT, Claude AI, and Google Gemini. This plan covers 8 feature areas prioritized by impact and complexity.

**Version Target:** v1.1.0
**Estimated Scope:** Medium-Large
**Priority:** High (improves core user experience)

---

## Current State

The Ask AI tab (`dashboard/frontend/src/components/ChatPanel.vue`) already has:
- Basic chat with Gemini API (non-streaming)
- Copy message, regenerate, edit user message (v1.0.11)
- Cancel button with thinking indicator and elapsed time
- Source citations (collapsible list, clickable to navigate)
- Markdown rendering with `marked.js`

**Files involved:**
- `dashboard/frontend/src/components/ChatPanel.vue` - Main chat UI
- `dashboard/frontend/src/services/api.ts` - API client with axios
- `dashboard/backend/chat_service.py` - Gemini API integration
- `dashboard/backend/main.py` - FastAPI routes

---

## Feature Enhancements

### Phase 1: Source Citation Enhancements (Priority: Highest)

**1.1 Hover Preview Tooltip**

Show memory details on hover over source citations.

```vue
<!-- SourceTooltip.vue component -->
<template>
  <div
    class="absolute z-50 w-80 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-xl border"
    :style="{ top: position.y + 'px', left: position.x + 'px' }"
  >
    <div class="flex items-center gap-2 mb-2">
      <span :class="typeColorClass" class="px-2 py-0.5 text-xs rounded">
        {{ source.type }}
      </span>
      <span class="text-xs text-gray-500">{{ source.id.slice(0, 12) }}...</span>
    </div>
    <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-4">
      {{ source.content_preview }}
    </p>
    <div v-if="source.tags?.length" class="mt-2 flex flex-wrap gap-1">
      <span v-for="tag in source.tags.slice(0, 5)" :key="tag"
            class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
        {{ tag }}
      </span>
    </div>
  </div>
</template>
```

**Implementation:**
1. Create `SourceTooltip.vue` component
2. Add `@mouseenter` / `@mouseleave` handlers to source items
3. Track mouse position for tooltip placement
4. Debounce hover (200ms) to prevent flicker

**1.2 Inline Memory References**

Parse AI response for memory references and make them clickable.

```typescript
// Update prompt to request structured references
const prompt = `...
When referencing memories, use the format [[Memory N]] where N is the memory number.
...`

// Parse response to convert [[Memory 1]] to clickable links
function parseMemoryReferences(text: string, sources: ChatSource[]): string {
  return text.replace(/\[\[Memory (\d+)\]\]/g, (match, num) => {
    const idx = parseInt(num) - 1
    if (sources[idx]) {
      return `<a href="#" class="memory-ref" data-memory-id="${sources[idx].id}">[Memory ${num}]</a>`
    }
    return match
  })
}
```

**1.3 Type-Colored Source Badges**

Apply consistent colors matching memory type badges.

```typescript
const TYPE_COLORS: Record<string, string> = {
  decision: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  solution: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  fact: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  preference: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  progress: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
}
```

---

### Phase 2: Save Conversation as Memory (Priority: High)

**2.1 Backend: New Memory Type**

Add `conversation` as a valid memory type.

```python
# In models.py or memory types
MEMORY_TYPES = [
    "fact", "decision", "solution", "error",
    "progress", "preference", "conversation", "other"
]
```

**2.2 Backend: Conversation Save Endpoint**

```python
# In main.py
@app.post("/api/chat/save")
async def save_conversation(
    project: str = Query(...),
    conversation: ConversationSave = Body(...)
):
    """Save a chat conversation as a memory."""
    # Format conversation into markdown
    content = format_conversation_markdown(conversation.messages)

    # Extract summary using Gemini
    summary = await generate_summary(conversation.messages)

    # Create memory
    memory_id = create_memory(
        db_path=project,
        content=content,
        memory_type="conversation",
        context=f"Chat conversation: {summary}",
        tags=["chat", "conversation"] + extract_topics(conversation.messages),
        importance=conversation.importance or 60,
        related_memory_ids=conversation.referenced_memory_ids
    )

    return {"memory_id": memory_id, "summary": summary}
```

**2.3 Frontend: Save Button**

```vue
<template>
  <button
    v-if="messages.length > 1"
    @click="saveConversation"
    class="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
    :disabled="isSaving"
  >
    <Bookmark v-if="!isSaved" class="w-4 h-4" />
    <Check v-else class="w-4 h-4" />
    {{ isSaved ? 'Saved' : 'Save Chat' }}
  </button>
</template>

<script setup>
async function saveConversation() {
  isSaving.value = true
  try {
    const referencedIds = messages.value
      .filter(m => m.sources)
      .flatMap(m => m.sources.map(s => s.id))

    const result = await api.saveConversation(store.currentDbPath, {
      messages: messages.value.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString()
      })),
      referenced_memory_ids: [...new Set(referencedIds)]
    })

    isSaved.value = true
    savedMemoryId.value = result.memory_id
    // Show toast notification
  } finally {
    isSaving.value = false
  }
}
</script>
```

---

### Phase 3: Response Streaming (Priority: High)

**3.1 Backend: SSE Streaming Endpoint**

```python
# In chat_service.py
async def stream_ask_about_memories(
    db_path: str,
    question: str,
    max_memories: int = 10,
):
    """Stream response using Gemini's streaming API."""
    # ... same setup as ask_about_memories ...

    model = get_model()

    # Yield sources first
    yield {
        "type": "sources",
        "data": sources
    }

    # Stream the response
    response = model.generate_content(prompt, stream=True)

    for chunk in response:
        if chunk.text:
            yield {
                "type": "chunk",
                "data": chunk.text
            }

    yield {
        "type": "done",
        "data": None
    }


# In main.py
from fastapi.responses import StreamingResponse
import json

@app.get("/api/chat/stream")
async def stream_chat(
    project: str = Query(...),
    question: str = Query(...),
    max_memories: int = Query(10)
):
    """SSE endpoint for streaming chat responses."""

    async def event_generator():
        async for event in stream_ask_about_memories(project, question, max_memories):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**3.2 Frontend: EventSource Handler**

```typescript
// In api.ts
export function streamChatResponse(
  dbPath: string,
  question: string,
  onChunk: (text: string) => void,
  onSources: (sources: ChatSource[]) => void,
  onDone: () => void,
  onError: (error: Error) => void
): () => void {
  const url = `/api/chat/stream?project=${encodeURIComponent(dbPath)}&question=${encodeURIComponent(question)}`

  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    switch (data.type) {
      case 'sources':
        onSources(data.data)
        break
      case 'chunk':
        onChunk(data.data)
        break
      case 'done':
        eventSource.close()
        onDone()
        break
    }
  }

  eventSource.onerror = (error) => {
    eventSource.close()
    onError(new Error('Stream connection failed'))
  }

  // Return cleanup function
  return () => eventSource.close()
}
```

**3.3 Frontend: Streaming UI**

```vue
<script setup>
const streamingContent = ref('')
const isStreaming = ref(false)

async function sendMessageStreaming() {
  isStreaming.value = true
  streamingContent.value = ''

  // Add placeholder assistant message
  const assistantMessage: Message = {
    id: `msg_${Date.now()}_assistant`,
    role: 'assistant',
    content: '',
    timestamp: new Date(),
    isStreaming: true
  }
  messages.value.push(assistantMessage)

  const cleanup = streamChatResponse(
    store.currentDbPath,
    question,
    (chunk) => {
      // Append chunk to streaming content
      assistantMessage.content += chunk
      scrollToBottom()
    },
    (sources) => {
      assistantMessage.sources = sources
    },
    () => {
      assistantMessage.isStreaming = false
      isStreaming.value = false
    },
    (error) => {
      assistantMessage.content = error.message
      assistantMessage.error = true
      isStreaming.value = false
    }
  )

  // Store cleanup for cancel functionality
  streamCleanup.value = cleanup
}
</script>
```

---

### Phase 4: Clickable Suggested Prompts (Priority: Medium)

**4.1 Make Example Prompts Clickable**

```vue
<template>
  <div v-if="messages.length === 0" class="suggestions">
    <p class="text-sm mb-3">Try asking:</p>
    <div class="flex flex-wrap gap-2">
      <button
        v-for="prompt in suggestedPrompts"
        :key="prompt"
        @click="inputValue = prompt; sendMessage()"
        class="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30
               text-blue-700 dark:text-blue-300 rounded-full
               hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
      >
        {{ prompt }}
      </button>
    </div>
  </div>
</template>

<script setup>
const suggestedPrompts = [
  "What decisions have I made about authentication?",
  "Summarize my recent solutions",
  "What errors have I encountered with Vue?",
  "Show me patterns I use frequently",
  "What are my coding preferences?"
]
</script>
```

**4.2 Follow-up Actions After Response**

```vue
<template>
  <!-- After assistant message -->
  <div v-if="!message.error && !isLoading" class="flex gap-2 mt-2">
    <button
      @click="sendFollowUp('Can you explain more?')"
      class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200"
    >
      Explain more
    </button>
    <button
      @click="sendFollowUp('Can you summarize this?')"
      class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200"
    >
      Summarize
    </button>
    <button
      @click="regenerateWithContext('Try a different approach')"
      class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200"
    >
      Different approach
    </button>
  </div>
</template>
```

---

### Phase 5: Conversation Export (Priority: Medium)

**5.1 Export Functions**

```typescript
// In ChatPanel.vue or a composable
function exportAsMarkdown(): string {
  let md = `# Chat Conversation\n`
  md += `**Project:** ${store.currentProject?.name}\n`
  md += `**Date:** ${new Date().toLocaleDateString()}\n\n---\n\n`

  for (const msg of messages.value) {
    const role = msg.role === 'user' ? '**You**' : '**Assistant**'
    const time = formatTime(msg.timestamp)
    md += `### ${role} (${time})\n\n${msg.content}\n\n`

    if (msg.sources?.length) {
      md += `**Sources:** ${msg.sources.map(s => s.id.slice(0, 8)).join(', ')}\n\n`
    }
    md += `---\n\n`
  }

  return md
}

function exportAsJson(): string {
  return JSON.stringify({
    project: store.currentDbPath,
    exportedAt: new Date().toISOString(),
    messages: messages.value.map(m => ({
      role: m.role,
      content: m.content,
      timestamp: m.timestamp.toISOString(),
      sources: m.sources
    }))
  }, null, 2)
}

function copyConversation() {
  const text = messages.value
    .map(m => `${m.role === 'user' ? 'You' : 'Assistant'}: ${m.content}`)
    .join('\n\n')
  navigator.clipboard.writeText(text)
}
```

**5.2 Export Menu UI**

```vue
<template>
  <div class="relative">
    <button @click="showExportMenu = !showExportMenu" class="p-2 rounded hover:bg-gray-200">
      <Download class="w-4 h-4" />
    </button>

    <div v-if="showExportMenu" class="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border z-50">
      <button @click="downloadMarkdown" class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100">
        Export as Markdown
      </button>
      <button @click="downloadJson" class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100">
        Export as JSON
      </button>
      <button @click="copyConversation" class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100">
        Copy to Clipboard
      </button>
    </div>
  </div>
</template>
```

---

### Phase 6: Keyboard Shortcuts (Priority: Medium-Low)

**6.1 Shortcuts Implementation**

```typescript
// useKeyboardShortcuts.ts composable
export function useChatKeyboardShortcuts(options: {
  onEscape: () => void
  onShowHelp: () => void
  onEditLastMessage: () => void
  inputRef: Ref<HTMLElement | null>
}) {
  function handleKeydown(e: KeyboardEvent) {
    // Escape: Cancel or clear
    if (e.key === 'Escape') {
      options.onEscape()
      return
    }

    // Ctrl+/ or Cmd+/: Show shortcuts help
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault()
      options.onShowHelp()
      return
    }

    // Up arrow with empty input: Edit last message
    if (e.key === 'ArrowUp' && options.inputRef.value) {
      const input = options.inputRef.value as HTMLTextAreaElement
      if (input.value === '' && input.selectionStart === 0) {
        e.preventDefault()
        options.onEditLastMessage()
      }
    }
  }

  onMounted(() => document.addEventListener('keydown', handleKeydown))
  onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
}
```

**6.2 Shortcuts Help Modal**

```vue
<template>
  <div v-if="showShortcutsHelp" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
      <h3 class="text-lg font-semibold mb-4">Keyboard Shortcuts</h3>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between"><span>Send message</span><kbd>Enter</kbd></div>
        <div class="flex justify-between"><span>New line</span><kbd>Shift + Enter</kbd></div>
        <div class="flex justify-between"><span>Cancel request</span><kbd>Escape</kbd></div>
        <div class="flex justify-between"><span>Edit last message</span><kbd>↑ (empty input)</kbd></div>
        <div class="flex justify-between"><span>Submit edit</span><kbd>Ctrl + Enter</kbd></div>
        <div class="flex justify-between"><span>This help</span><kbd>Ctrl + /</kbd></div>
      </div>
      <button @click="showShortcutsHelp = false" class="mt-4 w-full py-2 bg-blue-600 text-white rounded">
        Close
      </button>
    </div>
  </div>
</template>
```

---

### Phase 7: UI Polish (Priority: Low)

**7.1 Animated Typing Indicator**

```vue
<template>
  <div v-if="isStreaming" class="flex items-center gap-1">
    <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
    <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
    <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
  </div>
</template>

<style>
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}
.animate-bounce {
  animation: bounce 1.4s ease-in-out infinite;
}
</style>
```

**7.2 Relative Timestamps**

```typescript
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  return date.toLocaleDateString()
}
```

**7.3 Character Count**

```vue
<template>
  <div class="relative">
    <textarea v-model="inputValue" ... />
    <span class="absolute bottom-2 right-2 text-xs text-gray-400">
      {{ inputValue.length }} / 4000
    </span>
  </div>
</template>
```

---

### Phase 8: Search Within Chat (Priority: Low)

**8.1 Chat Search**

```vue
<script setup>
const searchQuery = ref('')
const searchResults = ref<number[]>([])
const currentSearchIndex = ref(0)

function searchChat() {
  if (!searchQuery.value) {
    searchResults.value = []
    return
  }

  const query = searchQuery.value.toLowerCase()
  searchResults.value = messages.value
    .map((m, i) => m.content.toLowerCase().includes(query) ? i : -1)
    .filter(i => i !== -1)

  currentSearchIndex.value = 0
  scrollToMessage(searchResults.value[0])
}

function highlightText(text: string): string {
  if (!searchQuery.value) return text
  const regex = new RegExp(`(${escapeRegex(searchQuery.value)})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>')
}
</script>
```

---

## File Changes Summary

| File | Changes |
|------|---------|
| `ChatPanel.vue` | All UI enhancements, new components |
| `api.ts` | Add `streamChatResponse`, `saveConversation` |
| `chat_service.py` | Add `stream_ask_about_memories` |
| `main.py` | Add `/api/chat/stream`, `/api/chat/save` endpoints |
| `models.py` | Add `conversation` to MEMORY_TYPES |
| `SourceTooltip.vue` | New component for hover preview |
| `useKeyboardShortcuts.ts` | New composable for shortcuts |

---

## Testing Strategy

### Unit Tests
- Test markdown parsing with memory references
- Test conversation export formatters
- Test keyboard shortcut handlers

### Integration Tests
- Test streaming endpoint with mocked Gemini
- Test save conversation flow
- Test source navigation

### Manual Testing Checklist
- [ ] Hover over source shows tooltip with content preview
- [ ] Click on inline memory reference navigates to memory
- [ ] Save conversation creates memory with correct type
- [ ] Streaming shows text appearing progressively
- [ ] Suggested prompts are clickable and send message
- [ ] Export produces valid Markdown/JSON
- [ ] All keyboard shortcuts work
- [ ] Search highlights matching text

---

## Success Criteria

1. **Source Citations**: Users can hover to preview and click to navigate to memories
2. **Save Conversation**: Chat can be saved as a searchable memory
3. **Streaming**: Response appears token-by-token like ChatGPT/Claude
4. **Discoverability**: Suggested prompts help new users get started
5. **Portability**: Conversations can be exported for backup/sharing
6. **Power Users**: Keyboard shortcuts speed up common actions
7. **Polish**: UI feels responsive and modern

---

## Implementation Order

| Phase | Feature | Complexity | Impact | Priority |
|-------|---------|------------|--------|----------|
| 1 | Source hover preview | Low | High | P0 |
| 1 | Inline clickable references | Medium | High | P0 |
| 2 | Save conversation | Medium | High | P1 |
| 3 | Response streaming | High | High | P1 |
| 4 | Clickable suggested prompts | Low | Medium | P2 |
| 5 | Export conversation | Low | Medium | P2 |
| 6 | Keyboard shortcuts | Medium | Medium | P3 |
| 7 | UI polish | Low | Low | P3 |
| 8 | Search within chat | Medium | Low | P4 |

**Recommended MVP:** Phases 1-2 (Source enhancements + Save conversation)
**Full Release:** Phases 1-5
**Nice to Have:** Phases 6-8

---

## References

- [ChatGPT UI patterns research](#) - Token streaming, branching, citations
- [Claude AI artifacts](#) - Side panel content, version control
- [Google Gemini features](#) - Source panel, hover previews, Gems
- [IndyDevDan patterns](mem_1767837897913) - Vue composables, WebSocket streaming
- [Current implementation](mem_1767983273508) - v1.0.11 Ask AI features
