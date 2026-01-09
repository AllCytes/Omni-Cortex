# Nano Banana Pro Image Generation Integration

## Overview

Integrate Google's Nano Banana Pro (gemini-3-pro-image-preview) image generation model into the Omni-CORTEX dashboard's Ask AI feature. Users can select specific memories as context, have a conversational back-and-forth to refine their request, and generate images like infographics, update sheets, or custom visuals based on memory content.

## Objectives

1. **Memory-Contextualized Generation**: Allow users to select memories that provide context for image generation
2. **Conversational Refinement**: Enable multi-turn conversations to refine image requests before generation
3. **Image Generation**: Generate high-quality images (infographics, update sheets, visuals) using Nano Banana Pro
4. **Download & Export**: Allow users to download generated images in various formats
5. **Seamless Integration**: Extend existing ChatPanel without breaking current functionality

## Technical Architecture

### Available Models

| Model | Codename | Model ID | Best For |
|-------|----------|----------|----------|
| **Nano Banana Pro** | Gemini 3 Pro Image | `gemini-3-pro-image-preview` | Professional asset production, complex instructions, up to 4K |
| **Nano Banana** | Gemini 2.5 Flash Image | `gemini-2.5-flash-image` | Speed/efficiency, high-volume, 1024px max |

### Model Configuration

```python
# Primary model for professional asset production
MODEL_ID = "gemini-3-pro-image-preview"

# Alternative for speed/efficiency
FLASH_MODEL_ID = "gemini-2.5-flash-image"

# Pricing (Nano Banana Pro):
# - Text input: $30 per 1M tokens
# - Image output: $30 per 1M tokens (1120 tokens per image for 1K/2K, 2000 for 4K)
```

### Key API Features

1. **Thinking Mode**: Model uses reasoning process to refine composition before generating (enabled by default, cannot be disabled)
   - Generates up to 2 interim "thought images" (visible in backend, not charged)
   - Last image in Thinking is the final rendered image

2. **Thought Signatures**: Required for multi-turn conversational editing
   - All `inline_data` parts with image mimetype have signatures
   - First non-thought text part has signature
   - Thoughts themselves do NOT have signatures
   - **SDK Chat feature handles signatures automatically**

3. **Up to 14 Reference Images** (Nano Banana Pro):
   - Up to 6 images of objects with high-fidelity
   - Up to 5 images of humans for character consistency
   - Flash model: up to 3 input images

4. **Google Search Grounding**: Generate images based on real-time data (weather, sports scores, current events)
   - Returns `groundingMetadata` with `searchEntryPoint` and `groundingChunks`

5. **High-Resolution Output**: 1K, 2K, and 4K generation (uppercase 'K' required)

6. **Advanced Text Rendering**: Legible, stylized text for infographics, menus, diagrams

7. **SynthID Watermark**: All generated images include invisible watermark

### Aspect Ratios & Resolution Tables

**Nano Banana Pro (gemini-3-pro-image-preview)**

| Aspect | 1K Resolution | 2K Resolution | 4K Resolution | 1K/2K Tokens | 4K Tokens |
|--------|---------------|---------------|---------------|--------------|-----------|
| 1:1    | 1024x1024     | 2048x2048     | 4096x4096     | 1120         | 2000      |
| 2:3    | 848x1264      | 1696x2528     | 3392x5056     | 1120         | 2000      |
| 3:2    | 1264x848      | 2528x1696     | 5056x3392     | 1120         | 2000      |
| 3:4    | 896x1200      | 1792x2400     | 3584x4800     | 1120         | 2000      |
| 4:3    | 1200x896      | 2400x1792     | 4800x3584     | 1120         | 2000      |
| 4:5    | 928x1152      | 1856x2304     | 3712x4608     | 1120         | 2000      |
| 5:4    | 1152x928      | 2304x1856     | 4608x3712     | 1120         | 2000      |
| 9:16   | 768x1376      | 1536x2752     | 3072x5504     | 1120         | 2000      |
| 16:9   | 1376x768      | 2752x1536     | 5504x3072     | 1120         | 2000      |
| 21:9   | 1584x672      | 3168x1344     | 6336x2688     | 1120         | 2000      |

**Nano Banana (gemini-2.5-flash-image)** - All 1290 tokens

| Aspect | Resolution |
|--------|------------|
| 1:1    | 1024x1024  |
| 2:3    | 832x1248   |
| 3:2    | 1248x832   |
| 3:4    | 864x1184   |
| 4:3    | 1184x864   |
| 4:5    | 896x1152   |
| 5:4    | 1152x896   |
| 9:16   | 768x1344   |
| 16:9   | 1344x768   |
| 21:9   | 1536x672   |

### Supported Languages (Best Performance)

EN, ar-EG, de-DE, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP, ko-KR, pt-BR, ru-RU, ua-UA, vi-VN, zh-CN

### Limitations

- No audio or video inputs supported
- May not follow exact number of requested images
- For text in images: generate text first, then ask for image with the text
- Image output count not guaranteed to match request

## Implementation Plan

### Phase 1: Backend - Image Generation Service

**File: `dashboard/backend/image_service.py`**

```python
"""Image generation service using Nano Banana Pro (gemini-3-pro-image-preview)."""

import os
import base64
from typing import Optional, List
from dataclasses import dataclass

from google import genai
from google.genai import types
from dotenv import load_dotenv

from database import get_memory_by_id
from models import Memory

load_dotenv()

@dataclass
class ImageGenerationResult:
    success: bool
    image_data: Optional[str] = None  # Base64 encoded
    mime_type: str = "image/png"
    text_response: Optional[str] = None
    thought_signature: Optional[str] = None
    error: Optional[str] = None

@dataclass
class ConversationTurn:
    role: str  # "user" or "model"
    text: Optional[str] = None
    image_data: Optional[str] = None
    thought_signature: Optional[str] = None

class ImageGenerationService:
    def __init__(self):
        self._api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client: Optional[genai.Client] = None
        self._conversation_history: List[ConversationTurn] = []

    def _get_client(self) -> Optional[genai.Client]:
        if self._client is None and self._api_key:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        return self._api_key is not None

    def build_memory_context(self, db_path: str, memory_ids: List[str]) -> str:
        """Build context string from selected memories."""
        memories = []
        for mem_id in memory_ids:
            memory = get_memory_by_id(db_path, mem_id)
            if memory:
                memories.append(f"""
Memory: {memory.memory_type}
Content: {memory.content}
Context: {memory.context or 'N/A'}
Tags: {', '.join(memory.tags) if memory.tags else 'N/A'}
""")
        return "\n---\n".join(memories)

    async def generate_image(
        self,
        prompt: str,
        memory_context: str,
        conversation_history: List[dict] = None,
        aspect_ratio: str = "16:9",
        image_size: str = "2K",
        use_search_grounding: bool = False,
    ) -> ImageGenerationResult:
        """Generate an image based on prompt and memory context."""
        client = self._get_client()
        if not client:
            return ImageGenerationResult(
                success=False,
                error="API key not configured"
            )

        # Build the full prompt with memory context
        full_prompt = f"""Based on the following memories/context:

{memory_context}

User request: {prompt}

Generate a professional, high-quality image that visualizes this information effectively."""

        # Build contents with conversation history for multi-turn
        contents = []
        if conversation_history:
            for turn in conversation_history:
                parts = []
                if turn.get("text"):
                    part = {"text": turn["text"]}
                    if turn.get("thought_signature"):
                        part["thoughtSignature"] = turn["thought_signature"]
                    parts.append(part)
                if turn.get("image_data"):
                    part = {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": turn["image_data"]
                        }
                    }
                    if turn.get("thought_signature"):
                        part["thoughtSignature"] = turn["thought_signature"]
                    parts.append(part)
                contents.append({
                    "role": turn["role"],
                    "parts": parts
                })

        # Add current prompt
        contents.append({
            "role": "user",
            "parts": [{"text": full_prompt}]
        })

        # Configure tools and image settings
        config = types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size
            )
        )

        if use_search_grounding:
            config.tools = [{"google_search": {}}]

        try:
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=contents,
                config=config
            )

            # Extract image and thought signatures
            image_data = None
            text_response = None
            thought_signature = None

            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = base64.b64encode(part.inline_data.data).decode()
                if hasattr(part, 'text') and part.text:
                    text_response = part.text
                if hasattr(part, 'thought_signature') and part.thought_signature:
                    thought_signature = part.thought_signature

            return ImageGenerationResult(
                success=True,
                image_data=image_data,
                text_response=text_response,
                thought_signature=thought_signature
            )

        except Exception as e:
            return ImageGenerationResult(
                success=False,
                error=str(e)
            )

    def clear_conversation(self):
        """Clear conversation history for new session."""
        self._conversation_history = []
```

### Phase 2: Backend - API Endpoints

**Update: `dashboard/backend/main.py`**

```python
from image_service import ImageGenerationService, ImageGenerationResult

image_service = ImageGenerationService()

class ImageGenerationRequest(BaseModel):
    prompt: str
    memory_ids: List[str] = []
    conversation_history: List[dict] = []
    aspect_ratio: str = "16:9"
    image_size: str = "2K"
    use_search_grounding: bool = False

class ImageGenerationResponse(BaseModel):
    success: bool
    image_data: Optional[str] = None
    text_response: Optional[str] = None
    thought_signature: Optional[str] = None
    error: Optional[str] = None

@app.get("/api/image/status")
async def get_image_status():
    """Check if image generation is available."""
    return {
        "available": image_service.is_available(),
        "message": "Image generation ready" if image_service.is_available()
                   else "Configure GEMINI_API_KEY for image generation"
    }

@app.post("/api/image/generate", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest, db_path: str = Query(...)):
    """Generate an image based on memories and prompt."""
    # Build memory context
    memory_context = ""
    if request.memory_ids:
        memory_context = image_service.build_memory_context(db_path, request.memory_ids)

    result = await image_service.generate_image(
        prompt=request.prompt,
        memory_context=memory_context,
        conversation_history=request.conversation_history,
        aspect_ratio=request.aspect_ratio,
        image_size=request.image_size,
        use_search_grounding=request.use_search_grounding
    )

    return ImageGenerationResponse(
        success=result.success,
        image_data=result.image_data,
        text_response=result.text_response,
        thought_signature=result.thought_signature,
        error=result.error
    )

@app.post("/api/image/clear-conversation")
async def clear_image_conversation():
    """Clear image generation conversation history."""
    image_service.clear_conversation()
    return {"status": "cleared"}
```

### Phase 3: Frontend - API Service

**Update: `dashboard/frontend/src/services/api.ts`**

```typescript
export interface ImageGenerationRequest {
  prompt: string
  memory_ids: string[]
  conversation_history: ConversationTurn[]
  aspect_ratio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4'
  image_size: '2K' | '4K'
  use_search_grounding: boolean
}

export interface ConversationTurn {
  role: 'user' | 'model'
  text?: string
  image_data?: string
  thought_signature?: string
}

export interface ImageGenerationResponse {
  success: boolean
  image_data?: string
  text_response?: string
  thought_signature?: string
  error?: string
}

export async function getImageStatus(dbPath: string): Promise<{ available: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/image/status?db_path=${encodeURIComponent(dbPath)}`)
  return response.json()
}

export async function generateImage(
  dbPath: string,
  request: ImageGenerationRequest
): Promise<ImageGenerationResponse> {
  const response = await fetch(`${API_BASE}/api/image/generate?db_path=${encodeURIComponent(dbPath)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  })
  return response.json()
}

export async function clearImageConversation(): Promise<void> {
  await fetch(`${API_BASE}/api/image/clear-conversation`, { method: 'POST' })
}
```

### Phase 4: Frontend - Image Generation Panel Component

**New File: `dashboard/frontend/src/components/ImageGenerationPanel.vue`**

Key features:
1. **Memory Selector**: Checkbox list to select memories as context
2. **Prompt Input**: Text area for describing desired image
3. **Settings Panel**: Aspect ratio, image size, grounding toggle
4. **Conversation View**: Shows back-and-forth refinement
5. **Image Preview**: Display generated image with download button
6. **Download Options**: PNG, JPEG with quality settings

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { generateImage, clearImageConversation, type ConversationTurn } from '@/services/api'
import {
  Image, Download, Settings, Loader2, RefreshCw,
  CheckSquare, Square, Sparkles, Search
} from 'lucide-vue-next'

const store = useDashboardStore()
const prompt = ref('')
const isGenerating = ref(false)
const selectedMemoryIds = ref<string[]>([])
const conversationHistory = ref<ConversationTurn[]>([])
const generatedImage = ref<string | null>(null)
const lastThoughtSignature = ref<string | null>(null)

// Settings
const aspectRatio = ref<'1:1' | '16:9' | '9:16' | '4:3' | '3:4'>('16:9')
const imageSize = ref<'2K' | '4K'>('2K')
const useSearchGrounding = ref(false)

const selectedMemories = computed(() =>
  store.memories.filter(m => selectedMemoryIds.value.includes(m.id))
)

async function handleGenerate() {
  if (!prompt.value.trim() || !store.currentDbPath) return

  isGenerating.value = true

  try {
    const result = await generateImage(store.currentDbPath, {
      prompt: prompt.value,
      memory_ids: selectedMemoryIds.value,
      conversation_history: conversationHistory.value,
      aspect_ratio: aspectRatio.value,
      image_size: imageSize.value,
      use_search_grounding: useSearchGrounding.value
    })

    if (result.success && result.image_data) {
      generatedImage.value = result.image_data

      // Update conversation history for multi-turn
      conversationHistory.value.push({
        role: 'user',
        text: prompt.value
      })

      conversationHistory.value.push({
        role: 'model',
        text: result.text_response,
        image_data: result.image_data,
        thought_signature: result.thought_signature
      })

      lastThoughtSignature.value = result.thought_signature
      prompt.value = ''
    }
  } finally {
    isGenerating.value = false
  }
}

function downloadImage(format: 'png' | 'jpeg' = 'png') {
  if (!generatedImage.value) return

  const link = document.createElement('a')
  link.href = `data:image/${format};base64,${generatedImage.value}`
  link.download = `omni-cortex-${Date.now()}.${format}`
  link.click()
}

async function startNewSession() {
  await clearImageConversation()
  conversationHistory.value = []
  generatedImage.value = null
  lastThoughtSignature.value = null
  prompt.value = ''
}

function toggleMemory(id: string) {
  const idx = selectedMemoryIds.value.indexOf(id)
  if (idx >= 0) {
    selectedMemoryIds.value.splice(idx, 1)
  } else {
    selectedMemoryIds.value.push(id)
  }
}
</script>
```

### Phase 5: Integration into ChatPanel

**Update: `dashboard/frontend/src/components/ChatPanel.vue`**

Add a toggle or tab system to switch between:
1. **Ask AI** (existing text chat)
2. **Generate Image** (new image generation mode)

```vue
<!-- Add mode toggle in header -->
<div class="flex gap-2">
  <button
    @click="mode = 'chat'"
    :class="mode === 'chat' ? 'bg-blue-600 text-white' : 'bg-gray-200'"
  >
    <MessageCircle class="w-4 h-4" />
    Chat
  </button>
  <button
    @click="mode = 'image'"
    :class="mode === 'image' ? 'bg-blue-600 text-white' : 'bg-gray-200'"
  >
    <Image class="w-4 h-4" />
    Generate
  </button>
</div>

<!-- Conditional rendering -->
<ChatContent v-if="mode === 'chat'" />
<ImageGenerationPanel v-else />
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
├─────────────────────────────────────────────────────────────┤
│  1. Select Memories  →  2. Enter Prompt  →  3. Configure   │
│     [☑ Memory 1]         "Create an          Aspect: 16:9  │
│     [☑ Memory 2]          infographic"       Size: 2K      │
│     [☐ Memory 3]                             [x] Grounding │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend Processing                         │
├─────────────────────────────────────────────────────────────┤
│  1. Fetch selected memories from SQLite                     │
│  2. Build context string from memory content                │
│  3. Construct prompt with context + user request            │
│  4. Include conversation history with thought signatures    │
│  5. Call gemini-3-pro-image-preview API                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Gemini 3 Pro Image (Nano Banana Pro)          │
├─────────────────────────────────────────────────────────────┤
│  - Processes context + prompt                               │
│  - Uses thinking to plan composition                        │
│  - Optional: Google Search for real-time data               │
│  - Generates image at specified resolution                  │
│  - Returns: image_data + thought_signature                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Response Handling                        │
├─────────────────────────────────────────────────────────────┤
│  1. Display generated image in preview                      │
│  2. Store thought_signature for conversational editing      │
│  3. Enable refinement: "Make the title bigger"              │
│  4. Download options: PNG, JPEG                             │
└─────────────────────────────────────────────────────────────┘
```

## Conversational Editing Flow

```
Turn 1: User → "Create infographic of my project decisions"
        Model ← [Image A] + thought_signature_1

Turn 2: User → "Make the colors more vibrant"
        (Include thought_signature_1 in request)
        Model ← [Image B] + thought_signature_2

Turn 3: User → "Add a timeline at the bottom"
        (Include thought_signature_2 in request)
        Model ← [Image C] + thought_signature_3
```

## Testing Strategy

### Unit Tests
- `test_image_service.py`: Mock Gemini API, test context building
- `test_image_endpoints.py`: FastAPI test client for endpoints

### Integration Tests
- End-to-end generation with real API (optional, requires key)
- Conversation history preservation
- Memory context injection

### Manual Testing
1. Generate image from single memory
2. Generate from multiple memories
3. Refine image through conversation
4. Test all aspect ratios and sizes
5. Test download functionality
6. Test error handling (no API key, API errors)

## Success Criteria

- [ ] Users can select memories as context for image generation
- [ ] Conversational back-and-forth refinement works (thought signatures preserved)
- [ ] Images generate successfully with various prompts
- [ ] All aspect ratio and size options work
- [ ] Download functionality works for PNG and JPEG
- [ ] Integration with existing Ask AI is seamless (tabbed interface)
- [ ] Error states are handled gracefully
- [ ] Loading states provide good UX feedback

## Potential Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Large memory context exceeding 65k tokens | Implement token counting and truncation with priority |
| Thought signature corruption | Strict preservation in conversation history state |
| Image generation latency (can be slow) | Loading skeleton, cancel option, background processing |
| API costs at scale | Rate limiting, usage tracking, optional confirmation for 4K |
| Browser memory with large images | Lazy loading, image compression for preview |

## Dependencies

### Python
- `google-genai` (already installed via google-generativeai)

### No new frontend dependencies required
- Uses existing Lucide icons
- Uses existing Tailwind styling

## Estimated Effort

| Phase | Complexity |
|-------|------------|
| Phase 1: Backend Service | Medium |
| Phase 2: API Endpoints | Low |
| Phase 3: Frontend API | Low |
| Phase 4: Image Panel Component | Medium-High |
| Phase 5: ChatPanel Integration | Low |
| Testing & Polish | Medium |

## Prompting Strategies & Templates

### 1. Photorealistic Scenes
Use photography terms: camera angles, lens types, lighting, fine details.

**Template:**
```
A photorealistic [shot type] of [subject], [action or expression], set in
[environment]. The scene is illuminated by [lighting description], creating
a [mood] atmosphere. Captured with a [camera/lens details], emphasizing
[key textures and details]. The image should be in a [aspect ratio] format.
```

### 2. Stylized Illustrations & Stickers
Be explicit about style and request transparent background.

**Template:**
```
A [style] sticker of a [subject], featuring [key characteristics] and a
[color palette]. The design should have [line style] and [shading style].
The background must be transparent.
```

### 3. Accurate Text in Images
Clear about text content, font style, and overall design.

**Template:**
```
Create a [image type] for [brand/concept] with the text "[text to render]"
in a [font style]. The design should be [style description], with a
[color scheme].
```

### 4. Product Mockups & Commercial Photography
Professional product shots for e-commerce, advertising, branding.

**Template:**
```
A high-resolution, studio-lit product photograph of a [product description]
on a [background surface/description]. The lighting is a [lighting setup,
e.g., three-point softbox setup] to [lighting purpose]. The camera angle is
a [angle type] to showcase [specific feature]. Ultra-realistic, with sharp
focus on [key detail]. [Aspect ratio].
```

### 5. Adding/Removing Elements
Provide image and describe change - model matches style, lighting, perspective.

**Template:**
```
Using the provided image of [subject], please [add/remove/modify] [element]
to/from the scene. Ensure the change is [description of how the change should
integrate].
```

### 6. Inpainting (Semantic Masking)
Edit specific part while leaving rest untouched.

**Template:**
```
Using the provided image, change only the [specific element] to [new
element/description]. Keep everything else in the image exactly the same,
preserving the original style, lighting, and composition.
```

### 7. Style Transfer
Transfer artistic style from one image to another.

**Template:**
```
Apply the artistic style and color palette from the first image (the
[style reference]) to the content of the second image (the [content image]).
```

### 8. Virtual Try-On
Combine clothing with model photos.

**Template:**
```
Create a professional e-commerce fashion photo. Take the [garment] from the
first image and let the [person] from the second image wear it. Generate a
realistic [shot type] with [lighting/environment].
```

### 9. Character Consistency / 360 View
Generate multiple angles by including previous outputs.

**Template:**
```
A studio portrait of [person] against [background], [looking forward/in profile looking right/etc.]
```

### 10. Sketch to Finished Image
Refine rough sketches into polished images.

**Template:**
```
Turn this rough [medium] sketch of a [subject] into a [style description]
photo. Keep the [specific features] from the sketch but add [new details/materials].
```

## Best Practices

1. **Be Hyper-Specific**: Instead of "fantasy armor," describe "ornate elven plate armor, etched with silver leaf patterns, with a high collar and pauldrons shaped like falcon wings."

2. **Provide Context and Intent**: Explain the purpose - "Create a logo for a high-end, minimalist skincare brand" yields better results than just "Create a logo."

3. **Iterate and Refine**: Use conversational nature for small changes - "That's great, but can you make the lighting a bit warmer?"

4. **Use Step-by-Step Instructions**: For complex scenes, break into steps - "First, create a background... Then, in the foreground, add... Finally, place..."

5. **Use "Semantic Negative Prompts"**: Instead of "no cars," describe positively: "an empty, deserted street with no signs of traffic."

6. **Control the Camera**: Use photographic/cinematic language - `wide-angle shot`, `macro shot`, `low-angle perspective`, `85mm portrait lens`, `bokeh`.

7. **Text Generation Order**: When generating text for images, first generate the text content, then ask for an image with the text.

## Use Cases for Omni-CORTEX Dashboard

### Memory Visualization
- **Decision Timeline**: "Create a visual timeline infographic showing the key decisions from these memories, with dates and brief descriptions"
- **Architecture Diagram**: "Generate a system architecture diagram based on the technical decisions in these memories"
- **Progress Report**: "Create a one-page visual progress report summarizing these project updates"

### Knowledge Export
- **Infographic Summary**: "Create an infographic summarizing the key learnings from these memories"
- **Comparison Chart**: "Generate a comparison chart showing the pros and cons discussed in these memories"
- **Workflow Diagram**: "Visualize the workflow described in these process memories"

### Status Updates
- **Project Status Card**: "Create a clean status card showing current project state based on these memories"
- **Metric Dashboard**: "Generate a visual dashboard showing the metrics mentioned in these memories"

## Future Enhancements

1. **Image History**: Store generated images with prompts for reference
2. **Templates**: Pre-built templates (infographic, timeline, comparison chart)
3. **Batch Generation**: Generate multiple variations
4. **Export to Memory**: Save generated image as a new memory attachment
5. **Collaborative Editing**: Share and refine images across sessions
6. **Reference Image Upload**: Allow users to upload reference images alongside memories
7. **Model Selection**: Toggle between Nano Banana Pro (quality) and Nano Banana (speed)
8. **Prompt Library**: Save and reuse successful prompts
9. **Generation Queue**: Background generation with notifications

---

**API Documentation Reference:** `docs/API Docs/Nano Banana Pro.md`
**Memory ID:** `mem_1767934538243_cb1cd2b3`
**Last Updated:** January 8, 2026
