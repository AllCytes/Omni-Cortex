<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import {
  getImageStatus,
  getImagePresets,
  generateImagesBatch,
  refineImage,
  clearImageConversation,
  type SingleImageRequest,
  type SingleImageResponse,
  type ImagePresetInfo,
  type AspectRatio,
  type ImageSize,
  type ImagePreset,
} from '@/services/api'
import {
  Image,
  Download,
  Loader2,
  RefreshCw,
  CheckSquare,
  Square,
  Sparkles,
  Search,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Pencil,
  ZoomIn,
  Archive,
} from 'lucide-vue-next'

const store = useDashboardStore()

// Service availability
const isAvailable = ref(false)
const statusMessage = ref('')
const presets = ref<ImagePresetInfo[]>([])

// Memory selection
const selectedMemoryIds = ref<string[]>([])
const memorySearchQuery = ref('')
const showMemoryPanel = ref(true)

// Image generation settings
const imageCount = ref<1 | 2 | 4>(1)
const imageRequests = ref<SingleImageRequest[]>([createDefaultRequest()])
const useSearchGrounding = ref(false)

// Chat context (passed from parent)
const props = defineProps<{
  chatMessages?: Array<{ role: string; content: string }>
}>()

// Generation state
const isGenerating = ref(false)
const generatedImages = ref<SingleImageResponse[]>([])
const generationErrors = ref<string[]>([])

// Edit modal
const editingImage = ref<SingleImageResponse | null>(null)
const editPrompt = ref('')
const isRefining = ref(false)

// Zoom modal
const zoomedImage = ref<SingleImageResponse | null>(null)

// Filtered memories for selection panel
const filteredMemories = computed(() => {
  if (!memorySearchQuery.value.trim()) {
    return store.memories.slice(0, 50) // Limit to first 50
  }
  const query = memorySearchQuery.value.toLowerCase()
  return store.memories
    .filter(m =>
      m.content.toLowerCase().includes(query) ||
      m.memory_type.toLowerCase().includes(query) ||
      m.tags.some(t => t.toLowerCase().includes(query))
    )
    .slice(0, 50)
})

// Create default request with preset
function createDefaultRequest(preset: ImagePreset = 'custom'): SingleImageRequest {
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
    image_size: '2K' as ImageSize
  }
}

// Watch imageCount to adjust imageRequests array
watch(imageCount, (newCount) => {
  while (imageRequests.value.length < newCount) {
    imageRequests.value.push(createDefaultRequest())
  }
  while (imageRequests.value.length > newCount) {
    imageRequests.value.pop()
  }
})

// Update aspect ratio when preset changes
function onPresetChange(index: number, preset: string) {
  const presetInfo = presets.value.find(p => p.value === preset)
  if (presetInfo) {
    imageRequests.value[index].aspect_ratio = presetInfo.default_aspect
  }
}

// Memory selection helpers
function toggleMemory(id: string) {
  const idx = selectedMemoryIds.value.indexOf(id)
  if (idx >= 0) {
    selectedMemoryIds.value.splice(idx, 1)
  } else {
    selectedMemoryIds.value.push(id)
  }
}

function selectAllMemories() {
  selectedMemoryIds.value = filteredMemories.value.map(m => m.id)
}

function selectNoneMemories() {
  selectedMemoryIds.value = []
}

function isMemorySelected(id: string): boolean {
  return selectedMemoryIds.value.includes(id)
}

// Generate images
async function handleGenerate() {
  if (!store.currentDbPath || imageRequests.value.length === 0) return

  // Ensure at least one request has a prompt or memories selected
  const hasContext = selectedMemoryIds.value.length > 0 ||
    imageRequests.value.some(r => r.custom_prompt.trim())

  if (!hasContext) {
    generationErrors.value = ['Please select memories or enter a prompt']
    return
  }

  isGenerating.value = true
  generationErrors.value = []
  generatedImages.value = []

  try {
    const result = await generateImagesBatch(store.currentDbPath, {
      images: imageRequests.value,
      memory_ids: selectedMemoryIds.value,
      chat_messages: props.chatMessages || [],
      use_search_grounding: useSearchGrounding.value
    })

    generatedImages.value = result.images
    generationErrors.value = result.errors
  } catch (e) {
    generationErrors.value = [e instanceof Error ? e.message : 'Failed to generate images']
  } finally {
    isGenerating.value = false
  }
}

// Refine image
async function handleRefine() {
  if (!editingImage.value?.image_id || !editPrompt.value.trim()) return

  isRefining.value = true
  try {
    const result = await refineImage({
      image_id: editingImage.value.image_id,
      refinement_prompt: editPrompt.value
    })

    // Update the image in the gallery
    const idx = generatedImages.value.findIndex(img => img.image_id === editingImage.value?.image_id)
    if (idx >= 0 && result.success) {
      generatedImages.value[idx] = result
    }

    closeEditModal()
  } catch (e) {
    console.error('Refine failed:', e)
  } finally {
    isRefining.value = false
  }
}

// Download image
function downloadImage(image: SingleImageResponse, format: 'png' | 'jpeg' = 'png') {
  if (!image.image_data) return

  const link = document.createElement('a')
  link.href = `data:image/${format};base64,${image.image_data}`
  link.download = `omni-cortex-${image.image_id || Date.now()}.${format}`
  link.click()
}

// Download all as zip
async function downloadAllAsZip() {
  // For simplicity, download each image individually
  // A full implementation would use JSZip
  for (const img of generatedImages.value) {
    if (img.success && img.image_data) {
      downloadImage(img)
      await new Promise(r => setTimeout(r, 500)) // Small delay between downloads
    }
  }
}

// Edit modal
function openEditModal(image: SingleImageResponse) {
  editingImage.value = image
  editPrompt.value = ''
}

function closeEditModal() {
  editingImage.value = null
  editPrompt.value = ''
}

// Zoom modal
function openZoomModal(image: SingleImageResponse) {
  zoomedImage.value = image
}

function closeZoomModal() {
  zoomedImage.value = null
}

// New session
async function startNewSession() {
  await clearImageConversation()
  generatedImages.value = []
  generationErrors.value = []
  imageRequests.value = [createDefaultRequest()]
  imageCount.value = 1
}

// Type colors for memory badges
const TYPE_COLORS: Record<string, string> = {
  decision: 'bg-amber-100 text-amber-800',
  solution: 'bg-emerald-100 text-emerald-800',
  error: 'bg-red-100 text-red-800',
  fact: 'bg-blue-100 text-blue-800',
  preference: 'bg-purple-100 text-purple-800',
  progress: 'bg-cyan-100 text-cyan-800',
  conversation: 'bg-indigo-100 text-indigo-800',
  troubleshooting: 'bg-orange-100 text-orange-800',
  other: 'bg-gray-100 text-gray-800',
}

// Aspect ratio options
const aspectRatioOptions: AspectRatio[] = ['1:1', '16:9', '9:16', '4:3', '3:4', '4:5', '5:4', '2:3', '3:2', '21:9']
const imageSizeOptions: ImageSize[] = ['1K', '2K', '4K']

// Load status and presets on mount
onMounted(async () => {
  try {
    const status = await getImageStatus()
    isAvailable.value = status.available
    statusMessage.value = status.message

    if (status.available) {
      const presetsResult = await getImagePresets()
      presets.value = presetsResult.presets
    }
  } catch (e) {
    statusMessage.value = 'Failed to check image generation status'
  }
})
</script>

<template>
  <div class="h-full flex">
    <!-- Memory Selection Side Panel -->
    <div
      v-if="showMemoryPanel"
      class="w-72 border-r border-gray-200 bg-gray-50 flex flex-col overflow-hidden"
    >
      <div class="p-3 border-b border-gray-200">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-medium text-sm text-gray-700">Memory Context</h3>
          <button
            @click="showMemoryPanel = false"
            class="p-1 hover:bg-gray-200 rounded"
            title="Hide panel"
          >
            <ChevronDown class="w-4 h-4" />
          </button>
        </div>

        <div class="flex gap-2 mb-2">
          <button
            @click="selectAllMemories"
            class="flex-1 text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
          >
            <CheckSquare class="w-3 h-3 inline mr-1" />
            All
          </button>
          <button
            @click="selectNoneMemories"
            class="flex-1 text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            <Square class="w-3 h-3 inline mr-1" />
            None
          </button>
        </div>

        <div class="relative">
          <Search class="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="memorySearchQuery"
            type="text"
            placeholder="Search memories..."
            class="w-full pl-8 pr-2 py-1.5 text-sm border border-gray-200 rounded"
          />
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div
          v-for="memory in filteredMemories"
          :key="memory.id"
          @click="toggleMemory(memory.id)"
          class="p-2 rounded cursor-pointer transition-colors"
          :class="isMemorySelected(memory.id) ? 'bg-blue-100 border border-blue-300' : 'bg-white border border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-start gap-2">
            <component
              :is="isMemorySelected(memory.id) ? CheckSquare : Square"
              class="w-4 h-4 mt-0.5 flex-shrink-0"
              :class="isMemorySelected(memory.id) ? 'text-blue-600' : 'text-gray-400'"
            />
            <div class="flex-1 min-w-0">
              <span
                class="text-xs px-1.5 py-0.5 rounded"
                :class="TYPE_COLORS[memory.memory_type] || TYPE_COLORS.other"
              >
                {{ memory.memory_type }}
              </span>
              <p class="text-xs text-gray-600 mt-1 line-clamp-2">
                {{ memory.content.substring(0, 100) }}{{ memory.content.length > 100 ? '...' : '' }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="p-2 border-t border-gray-200 bg-white">
        <span class="text-xs text-gray-500">
          {{ selectedMemoryIds.length }} selected
        </span>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="p-4 border-b border-gray-200 bg-white">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <button
              v-if="!showMemoryPanel"
              @click="showMemoryPanel = true"
              class="p-2 hover:bg-gray-100 rounded"
              title="Show memory panel"
            >
              <ChevronUp class="w-4 h-4" />
            </button>
            <Image class="w-5 h-5 text-purple-600" />
            <h2 class="font-semibold text-gray-800">Image Generation</h2>
            <span
              class="text-xs px-2 py-0.5 rounded-full"
              :class="isAvailable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >
              {{ isAvailable ? 'Ready' : 'Unavailable' }}
            </span>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="startNewSession"
              class="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded"
            >
              <RefreshCw class="w-4 h-4" />
              New Session
            </button>
          </div>
        </div>

        <!-- Not available message -->
        <div v-if="!isAvailable" class="p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div class="flex items-start gap-2">
            <AlertCircle class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p class="text-sm text-amber-800">{{ statusMessage }}</p>
              <p class="text-xs text-amber-600 mt-1">
                Set GEMINI_API_KEY environment variable and install google-genai package.
              </p>
            </div>
          </div>
        </div>

        <!-- Image Count Selector -->
        <div v-if="isAvailable" class="mb-4">
          <label class="text-sm font-medium text-gray-700 mb-2 block">Number of Images</label>
          <div class="flex gap-2">
            <button
              v-for="count in [1, 2, 4] as const"
              :key="count"
              @click="imageCount = count"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="imageCount === count
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              {{ count }}
            </button>
          </div>
        </div>

        <!-- Image Request Cards -->
        <div v-if="isAvailable" class="grid gap-4" :class="imageCount === 1 ? '' : imageCount === 2 ? 'grid-cols-2' : 'grid-cols-2'">
          <div
            v-for="(request, index) in imageRequests"
            :key="index"
            class="p-3 border border-gray-200 rounded-lg bg-gray-50"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700">Image {{ index + 1 }}</span>
            </div>

            <!-- Preset Selector -->
            <div class="mb-2">
              <label class="text-xs text-gray-500 block mb-1">Preset</label>
              <select
                v-model="request.preset"
                @change="onPresetChange(index, request.preset)"
                class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded"
              >
                <option v-for="preset in presets" :key="preset.value" :value="preset.value">
                  {{ preset.label }}
                </option>
              </select>
            </div>

            <!-- Custom Prompt -->
            <div class="mb-2">
              <label class="text-xs text-gray-500 block mb-1">Custom Prompt</label>
              <textarea
                v-model="request.custom_prompt"
                placeholder="Describe what you want..."
                rows="2"
                class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded resize-none"
              />
            </div>

            <!-- Aspect Ratio & Size -->
            <div class="flex gap-2">
              <div class="flex-1">
                <label class="text-xs text-gray-500 block mb-1">Aspect</label>
                <select
                  v-model="request.aspect_ratio"
                  class="w-full px-2 py-1 text-xs border border-gray-200 rounded"
                >
                  <option v-for="ratio in aspectRatioOptions" :key="ratio" :value="ratio">
                    {{ ratio }}
                  </option>
                </select>
              </div>
              <div class="flex-1">
                <label class="text-xs text-gray-500 block mb-1">Size</label>
                <select
                  v-model="request.image_size"
                  class="w-full px-2 py-1 text-xs border border-gray-200 rounded"
                >
                  <option v-for="size in imageSizeOptions" :key="size" :value="size">
                    {{ size }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Search Grounding Toggle -->
        <div v-if="isAvailable" class="mt-4 flex items-center gap-2">
          <input
            type="checkbox"
            id="searchGrounding"
            v-model="useSearchGrounding"
            class="rounded"
          />
          <label for="searchGrounding" class="text-sm text-gray-600">
            Use Google Search grounding (for current events, real-time data)
          </label>
        </div>

        <!-- Generate Button -->
        <div v-if="isAvailable" class="mt-4">
          <button
            @click="handleGenerate"
            :disabled="isGenerating || !store.currentDbPath"
            class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Loader2 v-if="isGenerating" class="w-5 h-5 animate-spin" />
            <Sparkles v-else class="w-5 h-5" />
            {{ isGenerating ? 'Generating...' : 'Generate Images' }}
          </button>
        </div>
      </div>

      <!-- Generation Errors -->
      <div v-if="generationErrors.length > 0" class="p-4 bg-red-50 border-b border-red-200">
        <div v-for="(error, idx) in generationErrors" :key="idx" class="flex items-center gap-2 text-sm text-red-700">
          <AlertCircle class="w-4 h-4" />
          {{ error }}
        </div>
      </div>

      <!-- Generated Images Gallery -->
      <div class="flex-1 overflow-y-auto p-4">
        <div v-if="generatedImages.length > 0">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-medium text-gray-800">Generated Images ({{ generatedImages.length }})</h3>
            <button
              v-if="generatedImages.filter(i => i.success).length > 1"
              @click="downloadAllAsZip"
              class="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded"
            >
              <Archive class="w-4 h-4" />
              Download All
            </button>
          </div>

          <div
            class="grid gap-4"
            :class="generatedImages.length === 1 ? 'grid-cols-1' : generatedImages.length === 2 ? 'grid-cols-2' : 'grid-cols-2'"
          >
            <div
              v-for="image in generatedImages"
              :key="image.image_id || image.index"
              class="border border-gray-200 rounded-lg overflow-hidden bg-white"
            >
              <div v-if="image.success && image.image_data" class="relative group">
                <img
                  :src="`data:image/png;base64,${image.image_data}`"
                  :alt="`Generated image ${image.index + 1}`"
                  class="w-full h-auto cursor-pointer"
                  @click="openZoomModal(image)"
                />

                <!-- Overlay with actions -->
                <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <button
                    @click.stop="openZoomModal(image)"
                    class="p-2 bg-white rounded-full hover:bg-gray-100"
                    title="Zoom"
                  >
                    <ZoomIn class="w-5 h-5 text-gray-700" />
                  </button>
                  <button
                    @click.stop="openEditModal(image)"
                    class="p-2 bg-white rounded-full hover:bg-gray-100"
                    title="Edit"
                  >
                    <Pencil class="w-5 h-5 text-gray-700" />
                  </button>
                  <button
                    @click.stop="downloadImage(image)"
                    class="p-2 bg-white rounded-full hover:bg-gray-100"
                    title="Download"
                  >
                    <Download class="w-5 h-5 text-gray-700" />
                  </button>
                </div>
              </div>

              <div v-else class="p-4 flex items-center gap-2 text-red-600">
                <AlertCircle class="w-5 h-5" />
                <span class="text-sm">{{ image.error || 'Failed to generate' }}</span>
              </div>

              <!-- Text response if any -->
              <div v-if="image.text_response" class="p-2 border-t border-gray-100 text-xs text-gray-600">
                {{ image.text_response }}
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="h-full flex items-center justify-center">
          <div class="text-center text-gray-500">
            <Image class="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p class="text-sm">No images generated yet</p>
            <p class="text-xs mt-1">Select memories and configure your prompts above</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div
        v-if="editingImage"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="closeEditModal"
      >
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 overflow-hidden">
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="font-medium">Refine Image</h3>
            <button @click="closeEditModal" class="p-1 hover:bg-gray-100 rounded">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div class="p-4">
            <img
              v-if="editingImage.image_data"
              :src="`data:image/png;base64,${editingImage.image_data}`"
              alt="Image to edit"
              class="w-full max-h-64 object-contain rounded-lg mb-4"
            />

            <label class="block text-sm font-medium text-gray-700 mb-2">
              Refinement Prompt
            </label>
            <textarea
              v-model="editPrompt"
              placeholder="Describe changes you want (e.g., 'Make the title larger', 'Change colors to blue theme')"
              rows="3"
              class="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none"
            />
          </div>

          <div class="flex justify-end gap-2 p-4 border-t bg-gray-50">
            <button
              @click="closeEditModal"
              class="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
            <button
              @click="handleRefine"
              :disabled="isRefining || !editPrompt.trim()"
              class="flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-300"
            >
              <Loader2 v-if="isRefining" class="w-4 h-4 animate-spin" />
              Apply Edit
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Zoom Modal -->
    <Teleport to="body">
      <div
        v-if="zoomedImage"
        class="fixed inset-0 bg-black/90 flex items-center justify-center z-50"
        @click.self="closeZoomModal"
      >
        <button
          @click="closeZoomModal"
          class="absolute top-4 right-4 p-2 bg-white/20 rounded-full hover:bg-white/30"
        >
          <X class="w-6 h-6 text-white" />
        </button>

        <img
          v-if="zoomedImage.image_data"
          :src="`data:image/png;base64,${zoomedImage.image_data}`"
          alt="Zoomed image"
          class="max-w-[90vw] max-h-[90vh] object-contain"
        />

        <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
          <button
            @click="openEditModal(zoomedImage!)"
            class="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-100"
          >
            <Pencil class="w-4 h-4" />
            Edit
          </button>
          <button
            @click="downloadImage(zoomedImage!)"
            class="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-100"
          >
            <Download class="w-4 h-4" />
            Download
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>
