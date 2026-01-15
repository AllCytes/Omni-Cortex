# Response Composer Feature

> **Status:** Todo
> **Priority:** High
> **Estimated Time:** 3-4 hours
> **Dependencies:** Style Tab Dashboard Core (completed), Ask AI Style Integration (completed)

## Problem Statement

Users receive messages from various platforms (Skool posts, DMs, emails, comment threads) and need to respond in a way that:
1. Matches their personal communication style
2. Leverages their domain knowledge stored in memories
3. Uses analogies and examples typical of their voice
4. Maintains consistency across platforms

Currently, the "Write in My Style" toggle only affects tone/style but doesn't provide a structured workflow for:
- Pasting incoming messages
- Understanding the context/question being asked
- Generating knowledge-grounded responses
- Adjusting tone for different platforms

## Objectives

1. **Input Area** - Dedicated space to paste incoming messages with platform context
2. **Context Selector** - Platform type affects response format and tone defaults
3. **Response Generation** - AI generates responses using style profile + relevant memories
4. **Quick Templates** - Pre-built response patterns for common scenarios
5. **Tone Adjustment** - Fine-tune formality level for the response
6. **Response Management** - Preview, edit, copy, and save response history

## Technical Approach

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ResponseComposer.vue                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ Input Section   │  │ Output Section                   │  │
│  │                 │  │                                  │  │
│  │ [Context Type]  │  │ [Generated Response]             │  │
│  │ [Message Input] │  │ [Tone Slider]                    │  │
│  │ [Templates]     │  │ [Edit Area]                      │  │
│  │ [Generate Btn]  │  │ [Copy/Save Actions]              │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Response History                          │
└─────────────────────────────────────────────────────────────┘
```

### New Components

1. **ResponseComposer.vue** - Main component (new tab in ChatPanel or standalone)
2. **ResponseHistoryItem.vue** - Individual history entry display
3. **ToneSlider.vue** - Reusable tone adjustment component

### Backend Changes

1. **New Endpoint:** `POST /api/compose-response`
   - Accepts incoming message, context type, template, tone level
   - Returns AI-generated response with relevant memory sources

2. **Enhanced Style Context:** Modify `build_style_context_prompt()` to include:
   - Platform-specific formatting rules
   - Template-based response structures
   - Tone adjustment instructions

### Data Models

```python
# models.py
class ComposeRequest(BaseModel):
    incoming_message: str
    context_type: Literal["skool_post", "dm", "email", "comment", "general"]
    template: Optional[str] = None  # "answer", "guide", "redirect", "acknowledge"
    tone_level: int = 50  # 0=casual, 100=professional
    include_memories: bool = True

class ComposeResponse(BaseModel):
    response: str
    sources: list[ChatSource]
    style_applied: bool
    tone_level: int
    template_used: Optional[str]
```

```typescript
// types/index.ts
export type ContextType = 'skool_post' | 'dm' | 'email' | 'comment' | 'general'
export type ResponseTemplate = 'answer' | 'guide' | 'redirect' | 'acknowledge'

export interface ComposeRequest {
  incoming_message: string
  context_type: ContextType
  template?: ResponseTemplate
  tone_level: number
  include_memories: boolean
}

export interface ComposedResponse {
  id: string
  incoming_message: string
  response: string
  context_type: ContextType
  template_used?: ResponseTemplate
  tone_level: number
  sources: ChatSource[]
  created_at: string
}
```

## Implementation Phases

### Phase 1: Backend API (45 min)

**File: `dashboard/backend/main.py`**

```python
@app.post("/api/compose-response")
async def compose_response(
    request: ComposeRequest,
    project: str = Query(...),
):
    """Generate a response to an incoming message in user's style."""

    # 1. Load style profile
    style_profile = compute_style_profile_from_messages(project)

    # 2. Search relevant memories for context
    relevant_memories = []
    if request.include_memories:
        relevant_memories = search_memories(
            project,
            request.incoming_message,
            limit=5
        )

    # 3. Build enhanced prompt with:
    #    - Style profile context
    #    - Platform-specific formatting
    #    - Template structure
    #    - Tone adjustment

    # 4. Generate response via Gemini

    # 5. Return with sources
```

**File: `dashboard/backend/prompts.py`** (new file)

```python
PLATFORM_FORMATS = {
    "skool_post": "Skool community post - can be longer, use formatting, be educational",
    "dm": "Direct message - conversational, personal, concise",
    "email": "Email - professional greeting/closing, clear structure",
    "comment": "Comment reply - brief, direct, engaging",
    "general": "General response - balanced approach",
}

TEMPLATES = {
    "answer": "Directly answer their question with clear explanation",
    "guide": "Provide step-by-step guidance or recommendations",
    "redirect": "Acknowledge and redirect to a relevant resource",
    "acknowledge": "Acknowledge their point and add follow-up question",
}

def build_compose_prompt(
    incoming_message: str,
    style_profile: dict,
    context_type: str,
    template: str,
    tone_level: int,
    memories: list,
) -> str:
    """Build the full prompt for response composition."""
    ...
```

### Phase 2: Frontend Types & API (30 min)

**File: `dashboard/frontend/src/types/index.ts`**

Add new types for compose feature (shown above).

**File: `dashboard/frontend/src/services/api.ts`**

```typescript
export async function composeResponse(
  dbPath: string,
  request: ComposeRequest
): Promise<ComposedResponse> {
  const response = await api.post<ComposedResponse>(
    `/compose-response?project=${encodeURIComponent(dbPath)}`,
    request
  )
  return response.data
}

export async function getResponseHistory(
  dbPath: string,
  limit = 10
): Promise<ComposedResponse[]> {
  const response = await api.get<ComposedResponse[]>(
    `/response-history?project=${encodeURIComponent(dbPath)}&limit=${limit}`
  )
  return response.data
}
```

### Phase 3: ResponseComposer Component (90 min)

**File: `dashboard/frontend/src/components/ResponseComposer.vue`**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { composeResponse } from '@/services/api'
import type { ContextType, ResponseTemplate, ComposedResponse } from '@/types'
import {
  MessageSquare, Mail, Users, AtSign, FileText,
  Wand2, Copy, Check, History, Sparkles,
  SlidersHorizontal, RefreshCw
} from 'lucide-vue-next'

const store = useDashboardStore()

// Input state
const incomingMessage = ref('')
const contextType = ref<ContextType>('general')
const selectedTemplate = ref<ResponseTemplate | null>(null)
const toneLevel = ref(50) // 0-100 slider
const includeMemories = ref(true)

// Output state
const generatedResponse = ref('')
const isGenerating = ref(false)
const responseHistory = ref<ComposedResponse[]>([])
const copiedRecently = ref(false)

// Context type options with icons
const contextOptions = [
  { value: 'skool_post', label: 'Skool Post', icon: Users },
  { value: 'dm', label: 'Direct Message', icon: MessageSquare },
  { value: 'email', label: 'Email', icon: Mail },
  { value: 'comment', label: 'Comment Thread', icon: AtSign },
  { value: 'general', label: 'General', icon: FileText },
]

// Quick templates
const templates = [
  { value: 'answer', label: 'Answer Question', desc: 'Direct answer with explanation' },
  { value: 'guide', label: 'Provide Guidance', desc: 'Step-by-step recommendations' },
  { value: 'redirect', label: 'Redirect to Resource', desc: 'Point to helpful resource' },
  { value: 'acknowledge', label: 'Acknowledge & Follow-up', desc: 'Validate and ask more' },
]

// Tone labels
const toneLabel = computed(() => {
  if (toneLevel.value < 25) return 'Very Casual'
  if (toneLevel.value < 50) return 'Casual'
  if (toneLevel.value < 75) return 'Professional'
  return 'Very Professional'
})

async function generate() {
  if (!incomingMessage.value.trim() || !store.currentDbPath) return

  isGenerating.value = true
  try {
    const result = await composeResponse(store.currentDbPath, {
      incoming_message: incomingMessage.value,
      context_type: contextType.value,
      template: selectedTemplate.value || undefined,
      tone_level: toneLevel.value,
      include_memories: includeMemories.value,
    })

    generatedResponse.value = result.response
    responseHistory.value.unshift(result)
  } catch (e) {
    console.error('Failed to generate response:', e)
  } finally {
    isGenerating.value = false
  }
}

async function copyResponse() {
  await navigator.clipboard.writeText(generatedResponse.value)
  copiedRecently.value = true
  setTimeout(() => copiedRecently.value = false, 2000)
}

function regenerate() {
  generate()
}

function useHistoryItem(item: ComposedResponse) {
  generatedResponse.value = item.response
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <Wand2 class="w-5 h-5 text-indigo-500" />
        Response Composer
      </h2>
      <p class="text-sm text-gray-500 mt-1">
        Paste a message and generate a response in your voice
      </p>
    </div>

    <div class="flex-1 overflow-auto p-4">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left: Input Section -->
        <div class="space-y-4">
          <!-- Context Type Selector -->
          <div>
            <label class="block text-sm font-medium mb-2">Message Source</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="opt in contextOptions"
                :key="opt.value"
                @click="contextType = opt.value"
                :class="[
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                  contextType === opt.value
                    ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 ring-2 ring-indigo-500'
                    : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                ]"
              >
                <component :is="opt.icon" class="w-4 h-4" />
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Incoming Message Input -->
          <div>
            <label class="block text-sm font-medium mb-2">Incoming Message</label>
            <textarea
              v-model="incomingMessage"
              placeholder="Paste the message you want to respond to..."
              rows="8"
              class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 resize-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <!-- Quick Templates -->
          <div>
            <label class="block text-sm font-medium mb-2">Response Template (Optional)</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="tpl in templates"
                :key="tpl.value"
                @click="selectedTemplate = selectedTemplate === tpl.value ? null : tpl.value"
                :class="[
                  'p-3 rounded-lg text-left transition-colors',
                  selectedTemplate === tpl.value
                    ? 'bg-indigo-100 dark:bg-indigo-900/30 ring-2 ring-indigo-500'
                    : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                ]"
              >
                <div class="font-medium text-sm">{{ tpl.label }}</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ tpl.desc }}</div>
              </button>
            </div>
          </div>

          <!-- Options -->
          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="includeMemories" class="rounded" />
              <span class="text-sm">Include knowledge from memories</span>
            </label>
          </div>

          <!-- Generate Button -->
          <button
            @click="generate"
            :disabled="!incomingMessage.trim() || isGenerating"
            class="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
          >
            <Sparkles v-if="!isGenerating" class="w-5 h-5" />
            <RefreshCw v-else class="w-5 h-5 animate-spin" />
            {{ isGenerating ? 'Generating...' : 'Generate Response' }}
          </button>
        </div>

        <!-- Right: Output Section -->
        <div class="space-y-4">
          <!-- Tone Slider -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium flex items-center gap-2">
                <SlidersHorizontal class="w-4 h-4" />
                Tone Adjustment
              </label>
              <span class="text-sm text-indigo-600 dark:text-indigo-400 font-medium">
                {{ toneLabel }}
              </span>
            </div>
            <input
              type="range"
              v-model="toneLevel"
              min="0"
              max="100"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div class="flex justify-between text-xs text-gray-400 mt-1">
              <span>Casual</span>
              <span>Professional</span>
            </div>
          </div>

          <!-- Generated Response -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium">Generated Response</label>
              <div class="flex items-center gap-2">
                <button
                  v-if="generatedResponse"
                  @click="regenerate"
                  class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                  title="Regenerate"
                >
                  <RefreshCw class="w-4 h-4" />
                </button>
                <button
                  v-if="generatedResponse"
                  @click="copyResponse"
                  class="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                >
                  <Check v-if="copiedRecently" class="w-4 h-4" />
                  <Copy v-else class="w-4 h-4" />
                  {{ copiedRecently ? 'Copied!' : 'Copy' }}
                </button>
              </div>
            </div>
            <textarea
              v-model="generatedResponse"
              placeholder="Your response will appear here..."
              rows="12"
              class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 resize-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      <!-- Response History -->
      <div v-if="responseHistory.length > 0" class="mt-8">
        <h3 class="text-sm font-medium flex items-center gap-2 mb-3">
          <History class="w-4 h-4" />
          Recent Responses
        </h3>
        <div class="space-y-2">
          <button
            v-for="item in responseHistory.slice(0, 5)"
            :key="item.id"
            @click="useHistoryItem(item)"
            class="w-full p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="text-sm font-medium truncate">{{ item.incoming_message.slice(0, 60) }}...</div>
            <div class="text-xs text-gray-500 mt-1">
              {{ item.context_type }} | {{ item.template_used || 'No template' }}
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

### Phase 4: Integration (30 min)

**Option A: New Tab in ChatPanel Mode Toggle**

Add "Compose" as a third mode alongside "Chat" and "Generate":

```vue
<!-- In ChatPanel.vue header -->
<div class="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-0.5">
  <button @click="mode = 'chat'" ...>Chat</button>
  <button @click="mode = 'compose'" ...>Compose</button>
  <button @click="mode = 'image'" ...>Generate</button>
</div>

<!-- Render ResponseComposer when mode === 'compose' -->
<ResponseComposer v-if="mode === 'compose'" />
```

**Option B: Standalone Tab (Recommended)**

Add as separate tab in main navigation, after "Ask AI":
`Memories | Activity | Statistics | Style | Review | Graph | Ask AI | Compose`

## Database Schema (Optional Enhancement)

Store response history for persistence:

```sql
CREATE TABLE IF NOT EXISTS composed_responses (
    id TEXT PRIMARY KEY,
    incoming_message TEXT NOT NULL,
    response TEXT NOT NULL,
    context_type TEXT NOT NULL,
    template_used TEXT,
    tone_level INTEGER DEFAULT 50,
    source_ids TEXT,  -- JSON array of memory IDs used
    created_at TEXT NOT NULL
);
```

## Testing Strategy

### Unit Tests
- [ ] `build_compose_prompt()` generates correct prompt structure
- [ ] Tone level affects prompt instructions correctly
- [ ] Platform formats are applied properly

### Integration Tests
- [ ] `/api/compose-response` returns valid response
- [ ] Memory search integration works
- [ ] Style profile is applied to output

### Manual Tests
- [ ] Paste Skool post → Generate → Response matches user's voice
- [ ] Tone slider visibly affects output formality
- [ ] Templates produce structurally different responses
- [ ] Copy button works correctly
- [ ] History items can be reused

## Success Criteria

1. **Functional:** User can paste message, select context, generate response in < 5 seconds
2. **Quality:** Generated responses sound like the user's voice based on style profile
3. **Usability:** Clear workflow from paste → configure → generate → copy
4. **Knowledge-Grounded:** Responses incorporate relevant memories when available
5. **Flexible:** Tone slider produces noticeably different outputs at extremes

## Potential Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Response doesn't match user's style | Enhance style prompt with more examples from user_messages |
| Slow response generation | Add streaming support like existing chat |
| Memory search returns irrelevant results | Improve search query extraction from incoming message |
| Tone slider has no visible effect | Make tone instructions more explicit in prompt |

## Future Enhancements

1. **Platform-specific formatting** - Auto-format for Skool markdown, email signatures
2. **Response variations** - Generate 3 options to choose from
3. **Saved templates** - User-defined response templates
4. **Analytics** - Track which templates/tones are used most
5. **Thread context** - Paste entire conversation thread for context-aware responses
