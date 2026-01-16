# Response Composer Enhancements

## Overview

Enhance the existing Response Composer with user-requested features to improve usability and flexibility when composing responses.

## Key Objectives

1. **Custom Instructions Text Box** - Allow users to add their own thoughts, requirements, specific questions, or things they want included in the generated response
2. **Clear Button** - One-click reset for all input/output fields
3. **"Explain to Me" Feature** - Explain incoming messages in user's own words before generating a response
4. **UX Polish** - Additional improvements for better workflow

## Technical Approach

### 1. Backend Changes

#### A. Update ComposeRequest Model (`models.py`)

Add new fields to support custom instructions and explain mode:

```python
class ComposeRequest(BaseModel):
    """Request for composing a response in user's style."""

    incoming_message: str = Field(..., min_length=1, max_length=5000)
    context_type: str = Field(default="general")
    template: Optional[str] = None
    tone_level: int = Field(default=50, ge=0, le=100)
    include_memories: bool = Field(default=True)
    # NEW FIELDS
    custom_instructions: Optional[str] = Field(default=None, max_length=2000)
    include_explanation: bool = Field(default=False)
```

#### B. Update ComposeResponse Model (`models.py`)

Add explanation field to response:

```python
class ComposeResponse(BaseModel):
    """Response from compose endpoint."""

    id: str
    response: str
    sources: list[ChatSource]
    style_applied: bool
    tone_level: int
    template_used: Optional[str]
    incoming_message: str
    context_type: str
    created_at: str
    # NEW FIELDS
    custom_instructions: Optional[str] = None
    explanation: Optional[str] = None  # Explanation of incoming message
```

#### C. Update `build_compose_prompt()` in `chat_service.py`

Modify the prompt builder to incorporate custom instructions:

```python
def build_compose_prompt(
    incoming_message: str,
    style_profile: Optional[dict],
    context_type: str,
    template: Optional[str],
    tone_level: int,
    memory_context: str,
    custom_instructions: Optional[str] = None,  # NEW
    include_explanation: bool = False,  # NEW
) -> str:
```

Add section to prompt:
```
## CUSTOM INSTRUCTIONS FROM USER

The user has provided these specific instructions for the response:
<custom_instructions>
{custom_instructions}
</custom_instructions>

Please incorporate these requirements while maintaining the user's voice.
```

For explanation mode, add to task section:
```
**Your Task:**
1. FIRST, provide a clear explanation of what the incoming message means or is asking
   Format: "**Understanding:** [your explanation in user's voice]"
2. THEN, write a response to the incoming message in YOUR voice
   Format: "**Response:** [your response]"
```

#### D. Update `compose_response()` function

- Pass new parameters through
- Parse response to extract explanation if `include_explanation=True`
- Split response into explanation + response parts when explanation mode is enabled

### 2. Frontend Changes

#### A. Update Types (`types/index.ts`)

```typescript
export interface ComposeRequest {
  incoming_message: string
  context_type: ContextType
  template?: ResponseTemplate
  tone_level: number
  include_memories: boolean
  custom_instructions?: string  // NEW
  include_explanation?: boolean  // NEW
}

export interface ComposedResponse {
  id: string
  response: string
  sources: ChatSource[]
  style_applied: boolean
  tone_level: number
  template_used?: ResponseTemplate
  incoming_message: string
  context_type: ContextType
  created_at: string
  custom_instructions?: string  // NEW
  explanation?: string  // NEW
}
```

#### B. Update ResponseComposer.vue

**New State Variables:**
```typescript
const customInstructions = ref('')
const includeExplanation = ref(false)
const explanation = ref('')
```

**New UI Elements:**

1. **Custom Instructions Text Area** (after Incoming Message):
```vue
<!-- Custom Instructions -->
<div>
  <label class="block text-sm font-medium mb-2">
    Your Instructions (Optional)
  </label>
  <textarea
    v-model="customInstructions"
    placeholder="Add specific requirements, questions to ask, or things to include in the response..."
    rows="3"
    class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 resize-none focus:ring-2 focus:ring-indigo-500"
  />
  <p class="text-xs text-gray-500 mt-1">
    E.g., "Ask them about their timeline" or "Include a resource link"
  </p>
</div>
```

2. **Include Explanation Checkbox** (in Options row):
```vue
<label class="flex items-center gap-2 cursor-pointer">
  <input type="checkbox" v-model="includeExplanation" class="rounded" />
  <span class="text-sm">Explain message to me first</span>
</label>
```

3. **Clear Button** (in header area):
```vue
<button
  @click="clearAll"
  class="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
>
  <Eraser class="w-4 h-4" />
  Clear All
</button>
```

4. **Explanation Section** (above Generated Response when present):
```vue
<div v-if="explanation" class="mb-4">
  <label class="block text-sm font-medium mb-2 flex items-center gap-2">
    <HelpCircle class="w-4 h-4 text-blue-500" />
    What This Message Means
  </label>
  <div class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm">
    {{ explanation }}
  </div>
</div>
```

**New Functions:**

```typescript
function clearAll() {
  incomingMessage.value = ''
  customInstructions.value = ''
  contextType.value = 'general'
  selectedTemplate.value = null
  toneLevel.value = 50
  includeMemories.value = true
  includeExplanation.value = false
  generatedResponse.value = ''
  explanation.value = ''
  errorMessage.value = ''
}
```

**Update generate() function:**
```typescript
async function generate() {
  // ...existing validation...

  const result = await composeResponse(store.currentDbPath, {
    incoming_message: incomingMessage.value,
    context_type: contextType.value,
    template: selectedTemplate.value || undefined,
    tone_level: toneLevel.value,
    include_memories: includeMemories.value,
    custom_instructions: customInstructions.value || undefined,  // NEW
    include_explanation: includeExplanation.value,  // NEW
  })

  generatedResponse.value = result.response
  explanation.value = result.explanation || ''  // NEW
  // ...rest of function...
}
```

#### C. Update API Service (`api.ts`)

Update the `composeResponse` function to include new fields in the request payload.

### 3. UI Layout Updates

Reorganize the left panel for better flow:

```
[Message Source selector]
[Incoming Message textarea]
[Custom Instructions textarea]  <- NEW
[Response Template grid]
[Options row: Include memories | Explain message] <- UPDATED
[Generate Button]  [Clear Button] <- Clear is NEW
```

Output panel (right):
```
[Tone Slider]
[Explanation card] <- NEW (shown when explanation exists)
[Generated Response textarea]
[Copy | Regenerate buttons]
```

## Implementation Steps

### Phase 1: Backend (15 min)
1. Update `ComposeRequest` model with `custom_instructions` and `include_explanation`
2. Update `ComposeResponse` model with `explanation` field
3. Update `build_compose_prompt()` to incorporate custom instructions
4. Add explanation parsing logic when `include_explanation=True`
5. Update endpoint handler

### Phase 2: Frontend Types (5 min)
1. Update `ComposeRequest` interface
2. Update `ComposedResponse` interface

### Phase 3: API Service (2 min)
1. Update `composeResponse()` to pass new fields

### Phase 4: Component Updates (25 min)
1. Add new state variables
2. Add custom instructions textarea
3. Add include explanation checkbox
4. Add clear button with icon
5. Add explanation display card
6. Update generate() function
7. Implement clearAll() function
8. Import new icons (Eraser, HelpCircle)

### Phase 5: Testing (10 min)
1. Test custom instructions flow
2. Test explanation mode
3. Test clear button
4. Test with/without style profile
5. Test response history with new fields

## Success Criteria

- [ ] Users can add custom instructions that get incorporated into generated responses
- [ ] "Explain to me" checkbox generates explanation before response
- [ ] Clear button resets all fields to default state
- [ ] Explanation appears in a distinct card above the response
- [ ] Response history stores custom instructions for replay
- [ ] All existing functionality continues to work

## Edge Cases

1. **Empty custom instructions** - Omit from prompt when empty
2. **Very long custom instructions** - 2000 char limit in backend
3. **Explanation parsing fails** - Return full response without explanation split
4. **No style profile** - Already handled (returns empty string for style context)

## Files to Modify

**Backend:**
- `dashboard/backend/models.py` - Add new fields to request/response models
- `dashboard/backend/chat_service.py` - Update prompt builder and compose function

**Frontend:**
- `dashboard/frontend/src/types/index.ts` - Update TypeScript interfaces
- `dashboard/frontend/src/services/api.ts` - Update API call
- `dashboard/frontend/src/components/ResponseComposer.vue` - Main component updates
