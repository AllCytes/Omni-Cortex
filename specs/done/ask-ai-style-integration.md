# Ask AI Style Integration

## Overview

Enhance the existing Ask AI (Chat) tab to incorporate user communication style awareness. This allows users to request content written in their own voice and enables style-aware AI responses.

**Prerequisite:** Style Tab Dashboard Core (spec #1) must be implemented first for the `/api/style-profile` endpoint.

## Objectives

1. Add "Write in My Style" toggle to ChatPanel
2. Add quick action buttons for style-related prompts
3. Integrate style profile context into AI chat requests
4. Display style mode indicator when active
5. Maintain existing chat functionality unchanged when style mode is off

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + TailwindCSS (existing ChatPanel.vue)
- **Backend**: FastAPI chat_service.py (existing)
- **AI Integration**: Claude API with style context injection

---

## Phase 1: Backend Enhancement

### 1.1 Update Chat Service (chat_service.py)

Modify `dashboard/backend/chat_service.py` to accept optional style context:

```python
async def chat_with_memories(
    query: str,
    project_path: str,
    conversation_history: list[dict] = None,
    style_context: dict | None = None,  # NEW PARAMETER
) -> AsyncGenerator[str, None]:
    """Chat with Claude using memory context and optional style profile."""

    # Build system prompt
    system_prompt = build_system_prompt(project_path)

    # If style context provided, inject it
    if style_context:
        style_section = build_style_context_prompt(style_context)
        system_prompt = f"{system_prompt}\n\n{style_section}"

    # ... rest of existing logic
```

### 1.2 Add Style Context Builder

Add to `dashboard/backend/chat_service.py`:

```python
def build_style_context_prompt(style_profile: dict) -> str:
    """Build a prompt section describing user's communication style."""

    tone_list = ", ".join(style_profile.get("tone_distribution", {}).keys())
    avg_words = style_profile.get("avg_word_count", 20)
    question_freq = style_profile.get("question_frequency", 0)

    markers = style_profile.get("key_markers", [])
    markers_text = "\n".join(f"- {m}" for m in markers) if markers else "- Direct and clear"

    return f"""
## User Communication Style Profile

When the user requests content "in their style" or "like they write", follow these patterns:

**Typical Message Length:** ~{int(avg_words)} words
**Common Tones:** {tone_list}
**Question Frequency:** {int(question_freq)}% of messages include questions

**Key Style Markers:**
{markers_text}

**Guidelines:**
- Match the user's typical message length and structure
- Use their common vocabulary patterns
- Mirror their tone and formality level
- If they're typically direct, be concise; if detailed, be comprehensive
"""
```

### 1.3 Update Chat Request Model

Modify `dashboard/backend/models.py`:

```python
class ChatRequest(BaseModel):
    query: str
    project: str
    conversation_id: Optional[str] = None
    use_style: bool = False  # NEW FIELD
```

### 1.4 Update Chat Endpoint

Modify the chat endpoint in `dashboard/backend/main.py`:

```python
@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    """Chat with Claude using memory context."""

    # If style mode enabled, fetch style profile
    style_context = None
    if request.use_style:
        try:
            style_context = get_style_profile(get_db_path(request.project))
        except Exception:
            pass  # Graceful fallback if no style data

    async def generate():
        async for chunk in chat_service.chat_with_memories(
            query=request.query,
            project_path=request.project,
            conversation_history=get_conversation_history(request.conversation_id),
            style_context=style_context,
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Phase 2: Frontend Enhancement

### 2.1 Update ChatPanel.vue

Modify `dashboard/frontend/src/components/ChatPanel.vue`:

#### Add Style Toggle State

```vue
<script setup lang="ts">
// Add to existing imports
import { Sparkles, User, Wand2 } from 'lucide-vue-next'
import { getStyleProfile } from '@/services/api'
import type { StyleProfile } from '@/types'

// Add new refs
const useStyleMode = ref(false)
const styleProfile = ref<StyleProfile | null>(null)
const loadingStyle = ref(false)

// Load style profile when toggled on
watch(useStyleMode, async (enabled) => {
  if (enabled && !styleProfile.value && store.currentProject) {
    loadingStyle.value = true
    try {
      styleProfile.value = await getStyleProfile(store.currentProject)
    } catch (e) {
      console.error('Failed to load style profile:', e)
      useStyleMode.value = false
    } finally {
      loadingStyle.value = false
    }
  }
})
</script>
```

#### Add Style Toggle UI

Add above the input area:

```vue
<!-- Style Mode Toggle -->
<div class="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
  <div class="flex items-center gap-4">
    <!-- Style Toggle -->
    <label class="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        v-model="useStyleMode"
        class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
      />
      <span class="text-sm font-medium flex items-center gap-1">
        <User class="w-4 h-4" />
        Write in My Style
      </span>
    </label>

    <!-- Style Active Indicator -->
    <span
      v-if="useStyleMode && styleProfile"
      class="text-xs px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-full flex items-center gap-1"
    >
      <Sparkles class="w-3 h-3" />
      Style: {{ Object.keys(styleProfile.tone_distribution)[0] || 'Active' }}
    </span>
  </div>

  <!-- Quick Actions -->
  <div class="flex items-center gap-2">
    <button
      @click="insertQuickPrompt('write-like-me')"
      class="text-xs px-3 py-1.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg flex items-center gap-1 transition-colors"
      title="Generate content in your style"
    >
      <Wand2 class="w-3 h-3" />
      Draft in my voice
    </button>
  </div>
</div>
```

#### Update Send Function

Modify the existing send function to include style flag:

```typescript
async function sendMessage() {
  if (!input.value.trim() || isLoading.value) return

  const userMessage = input.value.trim()
  input.value = ''

  messages.value.push({ role: 'user', content: userMessage })
  isLoading.value = true

  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: userMessage,
        project: store.currentProject,
        conversation_id: conversationId.value,
        use_style: useStyleMode.value,  // NEW
      }),
    })

    // ... rest of existing streaming logic
  } catch (e) {
    // ... error handling
  }
}
```

#### Add Quick Prompt Helper

```typescript
function insertQuickPrompt(type: string) {
  switch (type) {
    case 'write-like-me':
      input.value = 'Write the following in my communication style: '
      // Enable style mode automatically
      useStyleMode.value = true
      // Focus the input
      nextTick(() => {
        inputRef.value?.focus()
      })
      break
    case 'analyze-style':
      input.value = 'Analyze my communication style based on my message history and provide insights.'
      useStyleMode.value = true
      break
  }
}
```

### 2.2 Update Types (if needed)

Add to `dashboard/frontend/src/types/index.ts` if not already present from Spec #1:

```typescript
// Chat request with style support
export interface ChatRequestWithStyle {
  query: string
  project: string
  conversation_id?: string
  use_style?: boolean
}
```

---

## Phase 3: Visual Polish

### 3.1 Style Mode Active State

When style mode is enabled, add subtle visual indicator to the chat area:

```vue
<div
  :class="[
    'flex-1 overflow-y-auto p-4 space-y-4',
    useStyleMode ? 'bg-gradient-to-b from-indigo-50/30 to-transparent dark:from-indigo-900/10' : ''
  ]"
>
  <!-- Messages list -->
</div>
```

### 3.2 Loading State for Style Profile

```vue
<span v-if="loadingStyle" class="text-xs text-gray-500 flex items-center gap-1">
  <RefreshCw class="w-3 h-3 animate-spin" />
  Loading style...
</span>
```

---

## Testing Strategy

### Backend Tests

```python
def test_chat_without_style():
    """Test normal chat without style context."""
    pass

def test_chat_with_style():
    """Test chat with style context injection."""
    pass

def test_style_context_prompt_building():
    """Test style context prompt generation."""
    pass

def test_chat_style_fallback():
    """Test graceful fallback when no style data exists."""
    pass
```

### Frontend Manual Tests

1. [ ] Style toggle appears in ChatPanel
2. [ ] Toggle enables/disables style mode
3. [ ] Style indicator shows when mode is active
4. [ ] Quick action button inserts prompt and enables style
5. [ ] Chat request includes use_style flag when enabled
6. [ ] AI responses reflect user's style patterns
7. [ ] Graceful handling when no style profile exists
8. [ ] Dark mode styling correct
9. [ ] Style toggle state persists during conversation

---

## Success Criteria

1. **Functional**: Style context properly injected into AI prompts
2. **UX**: Toggle and indicator are intuitive and unobtrusive
3. **Performance**: Style profile loaded once and cached
4. **Fallback**: Chat works normally when style data unavailable
5. **Integration**: Works seamlessly with existing chat features

---

## File Checklist

### Backend
- [ ] `dashboard/backend/chat_service.py` - Add style context injection
- [ ] `dashboard/backend/models.py` - Update ChatRequest model
- [ ] `dashboard/backend/main.py` - Update /api/chat endpoint

### Frontend
- [ ] `dashboard/frontend/src/components/ChatPanel.vue` - Add style toggle, indicator, quick actions

---

## Implementation Order

1. Backend: Add style context builder function (10 min)
2. Backend: Update ChatRequest model (5 min)
3. Backend: Update chat endpoint (10 min)
4. Frontend: Add style toggle state and UI (20 min)
5. Frontend: Update send function (10 min)
6. Frontend: Add quick action helpers (10 min)
7. Visual polish and testing (15 min)

**Total: ~1.5 hours**

---

## Dependencies

- **Requires:** Style Tab Dashboard Core (spec #1) for `/api/style-profile` endpoint
- **Uses:** Existing ChatPanel.vue, chat_service.py infrastructure

---

## Notes

- Style context is injected into the system prompt, not user messages
- Style mode is per-session (not persisted across page reloads)
- Quick actions are convenience features, not requirements
- The AI interprets style guidance; results may vary
