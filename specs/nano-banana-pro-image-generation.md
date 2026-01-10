# Nano Banana Pro Image Generation Integration

## Overview

Integrate Google's Nano Banana Pro (gemini-3-pro-image-preview) image generation model into the Omni-CORTEX dashboard's Ask AI feature. The primary use case is **creating shareable content for social media** (Instagram, LinkedIn, Twitter/X, Skool) - including infographics, tip cards, workflow visualizations, and key insight summaries based on memory content and conversation context.

Users can toggle image generation mode in the chat, select memories from a side panel, generate multiple images with different purposes, and refine generated images through click-to-edit interactions.

## Objectives

1. **Social Media Content Creation**: Generate professional images optimized for posting on Instagram, LinkedIn, Twitter/X, and Skool
2. **Context-Aware Generation**: Pull context from current chat conversation AND selected memories
3. **Multi-Image Generation**: Generate 1, 2, or 4 images per request with granular control over each image's purpose
4. **Flexible Invocation**: Toggle image generation mode via input area button (alongside send button)
5. **Memory Selection Panel**: Side panel to browse, select all, or pick specific memories as context
6. **Project Context Switching**: Support global index search AND project-specific memory selection
7. **Click-to-Edit Refinement**: Click on any generated image to refine it with a follow-up prompt
8. **Download & Export**: Download generated images for social media posting
9. **Preset Templates**: Offer quick presets (Infographic, Key Insights, Tips & Tricks, Quote Card) with custom prompt override

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

## UI/UX Design

### Invocation Method: Toggle Button in Input Area

The image generation mode is activated via a **toggle button** in the Ask AI chat input area, positioned next to the send button.

```
┌─────────────────────────────────────────────────────────────────┐
│  Ask AI Chat Input Area                                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Type your message...                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [📷]  [➤ Send]                                                 │
│   ↑                                                              │
│   Toggle image generation mode                                   │
│   (icon changes to indicate active state)                        │
└─────────────────────────────────────────────────────────────────┘
```

**Toggle States:**
- **Off (default)**: Normal text chat mode, image icon is gray/outline
- **On**: Image generation mode, image icon is filled/highlighted, additional UI elements appear

### Memory Selection Side Panel

When image generation mode is active, a **collapsible side panel** appears showing available memories for context selection.

```
┌──────────────────────┬────────────────────────────────────────────┐
│ Memory Context       │  Chat / Image Generation Area              │
├──────────────────────┤                                            │
│ ☑ Select All         │  [Generated images appear here]            │
│ ☐ Select None        │                                            │
│                      │                                            │
│ 🔍 Search memories   │                                            │
├──────────────────────┤                                            │
│ Project: omni-cortex │                                            │
│ [Switch ▼]           │                                            │
├──────────────────────┤                                            │
│ ☑ Workflow pattern   │                                            │
│   discovered...      │                                            │
│ ☑ Claude Code tips   │                                            │
│   for productivity   │                                            │
│ ☐ API integration    │                                            │
│   decision...        │                                            │
│ ☑ Key insight about  │                                            │
│   hooks system...    │                                            │
│ ☐ Bug fix pattern    │                                            │
│   using Task agent   │                                            │
│                      │                                            │
│ [4 selected]         │                                            │
└──────────────────────┴────────────────────────────────────────────┘
```

**Features:**
- **Select All / Select None**: Quick bulk selection
- **Search**: Filter memories by keyword
- **Project Switcher**: Switch between projects or use Global Index
- **Memory Previews**: Show truncated content with tags
- **Selection Counter**: Shows how many memories are selected
- **Collapsible**: Can collapse panel to maximize chat area

### Multi-Image Generation with Granular Control

Users can generate 1, 2, or 4 images per request. Each image slot supports:
1. **Preset Template Selection** (quick start)
2. **Custom Prompt Override** (full control)

```
┌─────────────────────────────────────────────────────────────────┐
│ Image Generation Settings                                       │
├─────────────────────────────────────────────────────────────────┤
│ Number of Images: [1] [2] [4]                                   │
│                                                                  │
│ ┌─────────────────────────┐  ┌─────────────────────────────┐   │
│ │ Image 1                 │  │ Image 2                     │   │
│ ├─────────────────────────┤  ├─────────────────────────────┤   │
│ │ Preset: [Infographic ▼] │  │ Preset: [Key Insights ▼]   │   │
│ │                         │  │                             │   │
│ │ Custom prompt:          │  │ Custom prompt:              │   │
│ │ ┌─────────────────────┐ │  │ ┌─────────────────────────┐ │   │
│ │ │ Create a workflow   │ │  │ │ Show top 3 tips from    │ │   │
│ │ │ infographic showing │ │  │ │ these memories as a     │ │   │
│ │ │ my Claude Code...   │ │  │ │ clean list card...      │ │   │
│ │ └─────────────────────┘ │  │ └─────────────────────────┘ │   │
│ │                         │  │                             │   │
│ │ Aspect: [16:9 ▼]       │  │ Aspect: [1:1 ▼]            │   │
│ │ Size: [2K ▼]           │  │ Size: [2K ▼]               │   │
│ └─────────────────────────┘  └─────────────────────────────┘   │
│                                                                  │
│                    [Generate Images]                             │
└─────────────────────────────────────────────────────────────────┘
```

### Preset Templates

| Preset | Description | Default Aspect | Use Case |
|--------|-------------|----------------|----------|
| **Infographic** | Visual representation with icons, flow, hierarchy | 9:16 | Instagram Story, LinkedIn |
| **Key Insights** | Top 3-5 bullet points as clean card | 1:1 | Instagram Post |
| **Tips & Tricks** | Numbered tips with visual styling | 4:5 | Instagram Post |
| **Quote Card** | Standout quote with attribution | 1:1 | Twitter, LinkedIn |
| **Workflow** | Step-by-step process visualization | 16:9 | LinkedIn, Twitter |
| **Comparison** | Side-by-side or pros/cons layout | 16:9 | LinkedIn |
| **Summary Card** | Brief overview with key stats | 4:3 | Skool, LinkedIn |
| **Custom** | No preset, user provides full prompt | User choice | Any |

### Click-to-Edit Refinement

Generated images are clickable. Clicking opens an **edit modal** for refinement:

```
┌─────────────────────────────────────────────────────────────────┐
│ ✕ Edit Image                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │              [Generated Image Preview]                  │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Refinement prompt:                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Make the title larger and add a subtle gradient...      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Cancel]                    [Apply Edit]                        │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Shows current image large
- Text input for refinement prompt
- Preserves thought signatures for multi-turn editing
- History of edits for undo capability

### Conversation Context Integration

Image generation pulls context from **two sources**:

1. **Selected Memories** (from side panel)
2. **Current Chat Conversation** (recent messages)

```python
# Context building priority:
context = {
    "memories": selected_memories,           # User-selected from panel
    "conversation": recent_chat_messages,    # Last N messages from Ask AI chat
    "project": current_project_context       # Project-specific or global
}
```

This allows users to:
- Ask questions in chat about memories
- Then toggle image mode and generate visuals based on what was discussed
- Seamless flow from research → visualization

### Generated Images Gallery

After generation, images appear in a gallery view:

```
┌─────────────────────────────────────────────────────────────────┐
│ Generated Images (4)                                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │           │  │           │  │           │  │           │    │
│  │  Image 1  │  │  Image 2  │  │  Image 3  │  │  Image 4  │    │
│  │           │  │           │  │           │  │           │    │
│  ├───────────┤  ├───────────┤  ├───────────┤  ├───────────┤    │
│  │ [✏ Edit]  │  │ [✏ Edit]  │  │ [✏ Edit]  │  │ [✏ Edit]  │    │
│  │ [⬇ Save]  │  │ [⬇ Save]  │  │ [⬇ Save]  │  │ [⬇ Save]  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
│                                                                  │
│  [Download All as ZIP]           [Save All to Memory]           │
└─────────────────────────────────────────────────────────────────┘
```

**Per-Image Actions:**
- **Edit**: Opens click-to-edit modal
- **Save**: Download as PNG/JPEG

**Batch Actions:**
- **Download All**: Creates ZIP with all images
- **Save to Memory**: Optionally store generated images as memory attachments

## Implementation Plan

### Phase 1: Backend - Image Generation Service

**File: `dashboard/backend/image_service.py`**

```python
"""Image generation service using Nano Banana Pro (gemini-3-pro-image-preview)."""

import os
import base64
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum

from google import genai
from google.genai import types
from dotenv import load_dotenv

from database import get_memory_by_id
from models import Memory

load_dotenv()

class ImagePreset(str, Enum):
    """Preset templates for common image types."""
    INFOGRAPHIC = "infographic"
    KEY_INSIGHTS = "key_insights"
    TIPS_TRICKS = "tips_tricks"
    QUOTE_CARD = "quote_card"
    WORKFLOW = "workflow"
    COMPARISON = "comparison"
    SUMMARY_CARD = "summary_card"
    CUSTOM = "custom"

# Preset system prompts
PRESET_PROMPTS = {
    ImagePreset.INFOGRAPHIC: """Create a professional infographic with:
- Clear visual hierarchy with icons and sections
- Bold header/title at top
- 3-5 key points with visual elements
- Clean, modern design with good use of whitespace
- Professional color scheme""",

    ImagePreset.KEY_INSIGHTS: """Create a clean insights card showing:
- "Key Insights" or similar header
- 3-5 bullet points with key takeaways
- Each insight is concise (1-2 lines max)
- Clean typography, easy to read
- Subtle design elements""",

    ImagePreset.TIPS_TRICKS: """Create a tips card showing:
- Numbered tips (1, 2, 3, etc.) with icons
- Each tip is actionable and clear
- Visual styling that's engaging
- Good contrast and readability""",

    ImagePreset.QUOTE_CARD: """Create a quote card with:
- The key quote in large, styled text
- Attribution below the quote
- Elegant, minimalist design
- Suitable for social media sharing""",

    ImagePreset.WORKFLOW: """Create a workflow diagram showing:
- Step-by-step process with arrows/connectors
- Each step clearly labeled
- Visual flow from start to finish
- Professional diagrammatic style""",

    ImagePreset.COMPARISON: """Create a comparison visual showing:
- Side-by-side or pros/cons layout
- Clear distinction between options
- Visual indicators (checkmarks, icons)
- Balanced, professional presentation""",

    ImagePreset.SUMMARY_CARD: """Create a summary card with:
- Brief title/header
- Key stats or metrics highlighted
- Concise overview text
- Clean, scannable layout""",

    ImagePreset.CUSTOM: ""  # User provides full prompt
}

@dataclass
class SingleImageRequest:
    """Request for a single image within a batch."""
    preset: ImagePreset = ImagePreset.CUSTOM
    custom_prompt: str = ""
    aspect_ratio: str = "16:9"
    image_size: str = "2K"

@dataclass
class ImageGenerationResult:
    """Result for a single generated image."""
    success: bool
    image_data: Optional[str] = None  # Base64 encoded
    mime_type: str = "image/png"
    text_response: Optional[str] = None
    thought_signature: Optional[str] = None
    error: Optional[str] = None
    index: int = 0  # Position in batch

@dataclass
class BatchImageResult:
    """Result for batch image generation."""
    success: bool
    images: List[ImageGenerationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

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
        # Per-image conversation history for multi-turn editing
        self._image_conversations: Dict[str, List[ConversationTurn]] = {}

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

    def build_chat_context(self, chat_messages: List[dict]) -> str:
        """Build context string from recent chat conversation."""
        if not chat_messages:
            return ""

        context_parts = ["Recent conversation context:"]
        for msg in chat_messages[-10:]:  # Last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    def _build_prompt_with_preset(
        self,
        request: SingleImageRequest,
        memory_context: str,
        chat_context: str
    ) -> str:
        """Build full prompt combining preset, custom prompt, and context."""
        parts = []

        # Add memory context
        if memory_context:
            parts.append(f"Based on the following memories:\n\n{memory_context}")

        # Add chat context
        if chat_context:
            parts.append(f"\n{chat_context}")

        # Add preset prompt (if not custom)
        if request.preset != ImagePreset.CUSTOM:
            preset_prompt = PRESET_PROMPTS.get(request.preset, "")
            if preset_prompt:
                parts.append(f"\nImage style guidance:\n{preset_prompt}")

        # Add user's custom prompt
        if request.custom_prompt:
            parts.append(f"\nUser request: {request.custom_prompt}")

        parts.append("\nGenerate a professional, high-quality image optimized for social media sharing.")

        return "\n".join(parts)

    async def generate_single_image(
        self,
        request: SingleImageRequest,
        memory_context: str,
        chat_context: str = "",
        conversation_history: List[dict] = None,
        use_search_grounding: bool = False,
        image_id: str = None,
    ) -> ImageGenerationResult:
        """Generate a single image based on request and context."""
        client = self._get_client()
        if not client:
            return ImageGenerationResult(
                success=False,
                error="API key not configured"
            )

        # Build the full prompt
        full_prompt = self._build_prompt_with_preset(
            request, memory_context, chat_context
        )

        # Build contents with conversation history for multi-turn editing
        contents = []

        # Use image-specific conversation history if editing
        if image_id and image_id in self._image_conversations:
            for turn in self._image_conversations[image_id]:
                parts = []
                if turn.text:
                    part = {"text": turn.text}
                    if turn.thought_signature:
                        part["thoughtSignature"] = turn.thought_signature
                    parts.append(part)
                if turn.image_data:
                    part = {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": turn.image_data
                        }
                    }
                    if turn.thought_signature:
                        part["thoughtSignature"] = turn.thought_signature
                    parts.append(part)
                contents.append({
                    "role": turn.role,
                    "parts": parts
                })
        elif conversation_history:
            # Use provided conversation history
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

        # Configure image settings
        config = types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=request.aspect_ratio,
                image_size=request.image_size
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

            # Store conversation for this image (for editing)
            if image_id and image_data:
                if image_id not in self._image_conversations:
                    self._image_conversations[image_id] = []
                self._image_conversations[image_id].append(
                    ConversationTurn(role="user", text=full_prompt)
                )
                self._image_conversations[image_id].append(
                    ConversationTurn(
                        role="model",
                        text=text_response,
                        image_data=image_data,
                        thought_signature=thought_signature
                    )
                )

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

    async def generate_batch(
        self,
        requests: List[SingleImageRequest],
        memory_context: str,
        chat_context: str = "",
        use_search_grounding: bool = False,
    ) -> BatchImageResult:
        """Generate multiple images with different settings."""
        results = []
        errors = []

        for i, request in enumerate(requests):
            # Generate unique ID for each image in batch
            image_id = f"batch_{id(requests)}_{i}"

            result = await self.generate_single_image(
                request=request,
                memory_context=memory_context,
                chat_context=chat_context,
                use_search_grounding=use_search_grounding,
                image_id=image_id
            )
            result.index = i
            results.append(result)

            if not result.success:
                errors.append(f"Image {i+1}: {result.error}")

        return BatchImageResult(
            success=len(errors) == 0,
            images=results,
            errors=errors
        )

    async def refine_image(
        self,
        image_id: str,
        refinement_prompt: str,
        aspect_ratio: str = None,
        image_size: str = None
    ) -> ImageGenerationResult:
        """Refine an existing image using its conversation history."""
        client = self._get_client()
        if not client:
            return ImageGenerationResult(
                success=False,
                error="API key not configured"
            )

        if image_id not in self._image_conversations:
            return ImageGenerationResult(
                success=False,
                error="No conversation history found for this image"
            )

        # Build contents from conversation history
        contents = []
        last_turn = None

        for turn in self._image_conversations[image_id]:
            parts = []
            if turn.text:
                part = {"text": turn.text}
                if turn.thought_signature:
                    part["thoughtSignature"] = turn.thought_signature
                parts.append(part)
            if turn.image_data:
                part = {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": turn.image_data
                    }
                }
                if turn.thought_signature:
                    part["thoughtSignature"] = turn.thought_signature
                parts.append(part)
            contents.append({
                "role": turn.role,
                "parts": parts
            })
            last_turn = turn

        # Add refinement prompt
        contents.append({
            "role": "user",
            "parts": [{"text": refinement_prompt}]
        })

        # Use last known aspect ratio/size or defaults
        config = types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio or "16:9",
                image_size=image_size or "2K"
            )
        )

        try:
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=contents,
                config=config
            )

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

            # Update conversation history
            self._image_conversations[image_id].append(
                ConversationTurn(role="user", text=refinement_prompt)
            )
            self._image_conversations[image_id].append(
                ConversationTurn(
                    role="model",
                    text=text_response,
                    image_data=image_data,
                    thought_signature=thought_signature
                )
            )

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

    def clear_conversation(self, image_id: str = None):
        """Clear conversation history. If image_id provided, clear only that image."""
        if image_id:
            self._image_conversations.pop(image_id, None)
        else:
            self._image_conversations.clear()
```

### Phase 2: Backend - API Endpoints

**Update: `dashboard/backend/main.py`**

```python
from image_service import (
    ImageGenerationService,
    ImageGenerationResult,
    BatchImageResult,
    SingleImageRequest,
    ImagePreset
)

image_service = ImageGenerationService()

# Request/Response Models

class SingleImageRequestModel(BaseModel):
    preset: str = "custom"  # Maps to ImagePreset
    custom_prompt: str = ""
    aspect_ratio: str = "16:9"
    image_size: str = "2K"

class BatchImageGenerationRequest(BaseModel):
    """Request for generating multiple images."""
    images: List[SingleImageRequestModel]  # 1, 2, or 4 images
    memory_ids: List[str] = []
    chat_messages: List[dict] = []  # Recent chat for context
    use_search_grounding: bool = False

class ImageRefineRequest(BaseModel):
    """Request for refining an existing image."""
    image_id: str
    refinement_prompt: str
    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = None

class SingleImageResponseModel(BaseModel):
    success: bool
    image_data: Optional[str] = None
    text_response: Optional[str] = None
    thought_signature: Optional[str] = None
    image_id: Optional[str] = None  # For tracking/editing
    error: Optional[str] = None
    index: int = 0

class BatchImageGenerationResponse(BaseModel):
    success: bool
    images: List[SingleImageResponseModel] = []
    errors: List[str] = []

# Endpoints

@app.get("/api/image/status")
async def get_image_status():
    """Check if image generation is available."""
    return {
        "available": image_service.is_available(),
        "message": "Image generation ready" if image_service.is_available()
                   else "Configure GEMINI_API_KEY for image generation",
        "presets": [p.value for p in ImagePreset]
    }

@app.get("/api/image/presets")
async def get_image_presets():
    """Get available image preset templates."""
    return {
        "presets": [
            {"value": "infographic", "label": "Infographic", "default_aspect": "9:16"},
            {"value": "key_insights", "label": "Key Insights", "default_aspect": "1:1"},
            {"value": "tips_tricks", "label": "Tips & Tricks", "default_aspect": "4:5"},
            {"value": "quote_card", "label": "Quote Card", "default_aspect": "1:1"},
            {"value": "workflow", "label": "Workflow", "default_aspect": "16:9"},
            {"value": "comparison", "label": "Comparison", "default_aspect": "16:9"},
            {"value": "summary_card", "label": "Summary Card", "default_aspect": "4:3"},
            {"value": "custom", "label": "Custom", "default_aspect": "16:9"},
        ]
    }

@app.post("/api/image/generate-batch", response_model=BatchImageGenerationResponse)
async def generate_images_batch(
    request: BatchImageGenerationRequest,
    db_path: str = Query(...)
):
    """Generate multiple images with different presets/prompts."""
    # Validate image count
    if len(request.images) not in [1, 2, 4]:
        return BatchImageGenerationResponse(
            success=False,
            errors=["Must request 1, 2, or 4 images"]
        )

    # Build memory context
    memory_context = ""
    if request.memory_ids:
        memory_context = image_service.build_memory_context(db_path, request.memory_ids)

    # Build chat context
    chat_context = image_service.build_chat_context(request.chat_messages)

    # Convert request models to internal format
    image_requests = [
        SingleImageRequest(
            preset=ImagePreset(img.preset),
            custom_prompt=img.custom_prompt,
            aspect_ratio=img.aspect_ratio,
            image_size=img.image_size
        )
        for img in request.images
    ]

    result = await image_service.generate_batch(
        requests=image_requests,
        memory_context=memory_context,
        chat_context=chat_context,
        use_search_grounding=request.use_search_grounding
    )

    return BatchImageGenerationResponse(
        success=result.success,
        images=[
            SingleImageResponseModel(
                success=img.success,
                image_data=img.image_data,
                text_response=img.text_response,
                thought_signature=img.thought_signature,
                image_id=f"img_{i}_{id(result)}",
                error=img.error,
                index=img.index
            )
            for i, img in enumerate(result.images)
        ],
        errors=result.errors
    )

@app.post("/api/image/refine", response_model=SingleImageResponseModel)
async def refine_image(request: ImageRefineRequest):
    """Refine an existing generated image with a new prompt."""
    result = await image_service.refine_image(
        image_id=request.image_id,
        refinement_prompt=request.refinement_prompt,
        aspect_ratio=request.aspect_ratio,
        image_size=request.image_size
    )

    return SingleImageResponseModel(
        success=result.success,
        image_data=result.image_data,
        text_response=result.text_response,
        thought_signature=result.thought_signature,
        image_id=request.image_id,
        error=result.error
    )

@app.post("/api/image/clear-conversation")
async def clear_image_conversation(image_id: Optional[str] = None):
    """Clear image conversation history. If image_id provided, clear only that image."""
    image_service.clear_conversation(image_id)
    return {"status": "cleared", "image_id": image_id}
```

### Phase 3: Frontend - API Service

**Update: `dashboard/frontend/src/services/api.ts`**

```typescript
// Types
export type ImagePreset =
  | 'infographic'
  | 'key_insights'
  | 'tips_tricks'
  | 'quote_card'
  | 'workflow'
  | 'comparison'
  | 'summary_card'
  | 'custom'

export type AspectRatio = '1:1' | '16:9' | '9:16' | '4:3' | '3:4' | '4:5' | '5:4' | '2:3' | '3:2' | '21:9'
export type ImageSize = '1K' | '2K' | '4K'

export interface SingleImageRequest {
  preset: ImagePreset
  custom_prompt: string
  aspect_ratio: AspectRatio
  image_size: ImageSize
}

export interface BatchImageGenerationRequest {
  images: SingleImageRequest[]  // 1, 2, or 4 images
  memory_ids: string[]
  chat_messages: ChatMessage[]  // Recent chat for context
  use_search_grounding: boolean
}

export interface ImageRefineRequest {
  image_id: string
  refinement_prompt: string
  aspect_ratio?: AspectRatio
  image_size?: ImageSize
}

export interface SingleImageResponse {
  success: boolean
  image_data?: string
  text_response?: string
  thought_signature?: string
  image_id?: string
  error?: string
  index: number
}

export interface BatchImageGenerationResponse {
  success: boolean
  images: SingleImageResponse[]
  errors: string[]
}

export interface ImagePresetInfo {
  value: ImagePreset
  label: string
  default_aspect: AspectRatio
}

export interface ImageStatusResponse {
  available: boolean
  message: string
  presets: ImagePreset[]
}

// API Functions

export async function getImageStatus(): Promise<ImageStatusResponse> {
  const response = await fetch(`${API_BASE}/api/image/status`)
  return response.json()
}

export async function getImagePresets(): Promise<{ presets: ImagePresetInfo[] }> {
  const response = await fetch(`${API_BASE}/api/image/presets`)
  return response.json()
}

export async function generateImagesBatch(
  dbPath: string,
  request: BatchImageGenerationRequest
): Promise<BatchImageGenerationResponse> {
  const response = await fetch(
    `${API_BASE}/api/image/generate-batch?db_path=${encodeURIComponent(dbPath)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    }
  )
  return response.json()
}

export async function refineImage(
  request: ImageRefineRequest
): Promise<SingleImageResponse> {
  const response = await fetch(`${API_BASE}/api/image/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  })
  return response.json()
}

export async function clearImageConversation(imageId?: string): Promise<void> {
  const url = imageId
    ? `${API_BASE}/api/image/clear-conversation?image_id=${encodeURIComponent(imageId)}`
    : `${API_BASE}/api/image/clear-conversation`
  await fetch(url, { method: 'POST' })
}

// Helper to create default image requests
export function createDefaultImageRequest(preset: ImagePreset = 'custom'): SingleImageRequest {
  const presetDefaults: Record<ImagePreset, AspectRatio> = {
    infographic: '9:16',
    key_insights: '1:1',
    tips_tricks: '4:5',
    quote_card: '1:1',
    workflow: '16:9',
    comparison: '16:9',
    summary_card: '4:3',
    custom: '16:9'
  }

  return {
    preset,
    custom_prompt: '',
    aspect_ratio: presetDefaults[preset],
    image_size: '2K'
  }
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
┌──────────────────────────────────────────────────────────────────────────┐
│                          User Interface                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────┐     ┌─────────────────────────────────────────┐ │
│  │ Memory Selection    │     │  Image Configuration                    │ │
│  │ Side Panel          │     │                                         │ │
│  ├─────────────────────┤     │  Number of Images: [1] [2] [4]          │ │
│  │ ☑ Select All        │     │                                         │ │
│  │                     │     │  ┌─────────────┐  ┌─────────────┐       │ │
│  │ Project: omni-cortex│     │  │ Image 1     │  │ Image 2     │       │ │
│  │ [Switch ▼]          │     │  │ Preset: [▼] │  │ Preset: [▼] │       │ │
│  │                     │     │  │ Prompt:     │  │ Prompt:     │       │ │
│  │ ☑ Workflow tips     │     │  │ [________]  │  │ [________]  │       │ │
│  │ ☑ Key insights      │     │  │ Aspect: 1:1 │  │ Aspect: 16:9│       │ │
│  │ ☐ Decision log      │     │  └─────────────┘  └─────────────┘       │ │
│  │                     │     │                                         │ │
│  │ [3 selected]        │     │           [Generate Images]             │ │
│  └─────────────────────┘     └─────────────────────────────────────────┘ │
│                                                                           │
│  + Chat conversation context (last 10 messages) included automatically   │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Backend Processing                                │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Validate request (1, 2, or 4 images)                                 │
│  2. Fetch selected memories from SQLite (project-specific or global)     │
│  3. Build memory context string from content + tags                      │
│  4. Build chat context from recent conversation messages                 │
│  5. For each image in batch:                                             │
│     a. Apply preset template prompt (if not custom)                      │
│     b. Combine: memory context + chat context + preset + custom prompt   │
│     c. Call gemini-3-pro-image-preview API                               │
│     d. Store conversation history for later refinement                   │
│  6. Return batch results with image IDs for editing                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                  Gemini 3 Pro Image (Nano Banana Pro)                     │
├──────────────────────────────────────────────────────────────────────────┤
│  For each image request:                                                  │
│  - Processes combined context (memories + chat + preset + custom)         │
│  - Uses "Thinking Mode" to plan composition (interim thought images)      │
│  - Optional: Google Search grounding for real-time data                   │
│  - Generates image at specified aspect ratio and resolution               │
│  - Returns: image_data + thought_signature (for multi-turn editing)       │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Response & Gallery                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐             │
│  │  Image 1  │  │  Image 2  │  │  Image 3  │  │  Image 4  │             │
│  │ [Preview] │  │ [Preview] │  │ [Preview] │  │ [Preview] │             │
│  │ [✏ Edit]  │  │ [✏ Edit]  │  │ [✏ Edit]  │  │ [✏ Edit]  │             │
│  │ [⬇ Save]  │  │ [⬇ Save]  │  │ [⬇ Save]  │  │ [⬇ Save]  │             │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘             │
│                                                                           │
│  Click any image → Opens Edit Modal → Refinement prompt → Re-generate    │
│                                                                           │
│  [Download All as ZIP]                       [Save All to Memory]         │
└──────────────────────────────────────────────────────────────────────────┘
```

### Click-to-Edit Refinement Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User clicks on generated image                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Edit Modal Opens                                                │
│ - Shows current image large                                     │
│ - Text input for refinement prompt                              │
│ - "Make the title bigger", "Change colors to blue theme"        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: refine_image()                                         │
│ - Retrieves stored conversation history for this image_id       │
│ - Includes thought_signature for continuity                     │
│ - Sends refinement prompt with full context                     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Nano Banana Pro generates refined image                         │
│ - Understands previous context via thought_signature            │
│ - Makes targeted edits while maintaining style                  │
│ - Returns new image with new thought_signature                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Updated image replaces original in gallery                      │
│ - Conversation history updated for further edits                │
│ - User can continue refining with more prompts                  │
└─────────────────────────────────────────────────────────────────┘
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

### Core Functionality
- [ ] Toggle button in input area activates image generation mode
- [ ] Memory selection side panel shows with search and project switcher
- [ ] Users can select all, none, or specific memories as context
- [ ] Chat conversation context is automatically included in generation
- [ ] Images generate successfully for 1, 2, or 4 image batches

### Preset Templates
- [ ] All 8 presets available (Infographic, Key Insights, Tips & Tricks, Quote Card, Workflow, Comparison, Summary Card, Custom)
- [ ] Presets auto-select appropriate default aspect ratio
- [ ] Custom prompt can override/extend preset behavior

### Multi-Image Generation
- [ ] Each image slot has independent preset, prompt, aspect ratio, and size
- [ ] All aspect ratios work correctly (1:1, 16:9, 9:16, 4:3, 3:4, 4:5, 5:4, 2:3, 3:2, 21:9)
- [ ] All sizes work correctly (1K, 2K, 4K)

### Click-to-Edit Refinement
- [ ] Clicking generated image opens edit modal
- [ ] Refinement prompts modify image while maintaining style
- [ ] Thought signatures preserved for multi-turn editing
- [ ] Multiple refinements work in sequence

### Download & Export
- [ ] Individual image download works (PNG/JPEG)
- [ ] "Download All as ZIP" creates proper archive
- [ ] Downloaded images are social media ready (correct resolution)

### UX & Integration
- [ ] Integration with existing Ask AI is seamless
- [ ] Loading states provide good feedback (skeletons, progress indicators)
- [ ] Error states are handled gracefully with clear messages
- [ ] Memory selection panel is collapsible to maximize chat area

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

## Implementation Phases

| Phase | Description | Key Deliverables |
|-------|-------------|------------------|
| Phase 1 | Backend Image Service | `image_service.py` with batch generation, presets, refinement |
| Phase 2 | API Endpoints | Batch generate, refine, presets, status endpoints |
| Phase 3 | Frontend API Service | TypeScript types and API functions |
| Phase 4 | Image Generation Panel | Vue component with memory panel, image slots, gallery |
| Phase 5 | ChatPanel Integration | Toggle button, mode switching, context passing |
| Phase 6 | Testing & Polish | Unit tests, integration tests, UX refinements |

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

### Primary Use Case: Social Media Content Creation

The main purpose of this feature is to **turn your memories and learnings into shareable social media content**. Post your workflows, tips, and insights on Instagram, LinkedIn, Twitter/X, and Skool to share knowledge with your audience.

### Social Media Workflows

#### LinkedIn Posts
- **Preset**: Infographic (16:9) or Key Insights (1:1)
- **Example prompt**: "Create a LinkedIn-ready infographic showing my top 5 Claude Code productivity tips from these memories"
- **Use case**: Professional knowledge sharing, thought leadership

#### Instagram Posts
- **Preset**: Key Insights (1:1) or Tips & Tricks (4:5)
- **Example prompt**: "Make a clean, visually appealing tips card showing 3 ways I use hooks in Claude Code"
- **Use case**: Quick tips, bite-sized learnings

#### Instagram Stories
- **Preset**: Infographic (9:16)
- **Example prompt**: "Create a vertical story-style infographic showing my workflow for debugging with Claude Code"
- **Use case**: Step-by-step tutorials, process walkthroughs

#### Twitter/X Posts
- **Preset**: Quote Card (1:1) or Workflow (16:9)
- **Example prompt**: "Create a quote card with my key insight about using the Task agent effectively"
- **Use case**: Shareable quotes, quick wins

#### Skool Community Posts
- **Preset**: Summary Card (4:3) or Comparison (16:9)
- **Example prompt**: "Create a summary card showing what I learned this week about prompt engineering"
- **Use case**: Community updates, weekly learnings

### Multi-Image Social Campaigns

Generate multiple images at once for coordinated posts:

**Example: "Claude Code Tips Series"**
1. **Image 1** (Infographic, 9:16): "My complete workflow for using Claude Code hooks"
2. **Image 2** (Key Insights, 1:1): "Top 3 things I learned about the Task agent"
3. **Image 3** (Tips & Tricks, 4:5): "5 quick tips for better prompts"
4. **Image 4** (Quote Card, 1:1): "My favorite insight from this week"

### Knowledge Export & Documentation

#### Decision Documentation
- **Preset**: Workflow or Comparison
- **Example**: "Create a decision tree showing the technical choices I made for this project"

#### Learning Summaries
- **Preset**: Key Insights or Summary Card
- **Example**: "Summarize my key learnings from the past month into a visual card"

#### Process Visualization
- **Preset**: Workflow
- **Example**: "Show my step-by-step process for setting up a new project with Claude Code"

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
**Last Updated:** January 9, 2026
**Version:** 2.0 (Updated with social media focus, multi-image generation, click-to-edit refinement)
