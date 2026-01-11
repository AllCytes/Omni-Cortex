<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { MEMORY_TYPES } from '@/types'
import { useDashboardStore } from '@/stores/dashboardStore'
import { X, Plus, Loader2, Zap, Database } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'success', memory: { id: string; content: string }): void
}>()

const store = useDashboardStore()

// Form state
const content = ref('')
const memoryType = ref('decision')
const tagsInput = ref('')
const importance = ref(50)
const keepOpen = ref(false)
const isSaving = ref(false)

// Refs for DOM elements
const contentTextarea = ref<HTMLTextAreaElement | null>(null)

// Computed
const parsedTags = computed(() => {
  if (!tagsInput.value.trim()) return []
  return tagsInput.value.split(',').map(t => t.trim().toLowerCase()).filter(t => t.length > 0)
})

// Current project name for indicator
const projectName = computed(() => {
  return store.currentProject?.name || store.currentProject?.display_name || 'No project selected'
})

const hasProject = computed(() => {
  return !!store.currentProject
})

const canSave = computed(() => {
  return content.value.trim().length > 0 && !isSaving.value && hasProject.value
})

// Tag suggestions based on existing tags
const tagSuggestions = computed(() => {
  const input = tagsInput.value.split(',').pop()?.trim().toLowerCase() || ''
  if (!input || input.length < 1) return []

  return store.tags
    .filter(t => t.name.toLowerCase().startsWith(input))
    .filter(t => !parsedTags.value.includes(t.name.toLowerCase()))
    .slice(0, 5)
    .map(t => t.name)
})

const showSuggestions = ref(false)

// Reset form
function resetForm() {
  content.value = ''
  memoryType.value = 'decision'
  tagsInput.value = ''
  importance.value = 50
}

// Auto-focus content textarea when modal opens
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    contentTextarea.value?.focus()
  }
})

// Save memory
async function handleSave() {
  if (!canSave.value) return

  isSaving.value = true

  try {
    const created = await store.createMemory({
      content: content.value.trim(),
      memory_type: memoryType.value,
      importance_score: importance.value,
      tags: parsedTags.value,
    })

    if (created) {
      emit('success', { id: created.id, content: created.content })

      if (keepOpen.value) {
        resetForm()
        await nextTick()
        contentTextarea.value?.focus()
      } else {
        resetForm()
        emit('close')
      }
    }
  } finally {
    isSaving.value = false
  }
}

// Handle tag suggestion click
function addSuggestion(tag: string) {
  const parts = tagsInput.value.split(',')
  parts.pop()
  parts.push(tag)
  tagsInput.value = parts.join(', ') + ', '
  showSuggestions.value = false
}

// Handle blur with delay (to allow click on suggestions)
function handleTagsBlur() {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

// Close modal
function handleClose() {
  if (!isSaving.value) {
    resetForm()
    emit('close')
  }
}

// Handle Escape key
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    handleClose()
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    handleSave()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="handleClose"
      >
        <Transition
          enter-active-class="transition-all duration-200"
          leave-active-class="transition-all duration-200"
          enter-from-class="opacity-0 scale-95"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="isOpen"
            class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col"
          >
            <!-- Header -->
            <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-600 to-purple-600">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-white">
                  <Zap class="w-5 h-5" />
                  <h2 class="text-lg font-semibold">Quick Capture</h2>
                </div>
                <button
                  @click="handleClose"
                  :disabled="isSaving"
                  class="p-1 hover:bg-white/20 rounded transition-colors text-white disabled:opacity-50"
                >
                  <X class="w-5 h-5" />
                </button>
              </div>
              <!-- Project indicator -->
              <div class="flex items-center gap-1.5 mt-1.5 text-white/80 text-xs">
                <Database class="w-3 h-3" />
                <span>Saving to:</span>
                <span class="font-medium text-white">{{ projectName }}</span>
                <span v-if="!hasProject" class="text-yellow-200">(select a project first)</span>
              </div>
            </div>

            <!-- Form -->
            <div class="flex-1 overflow-y-auto p-5 space-y-4">
              <!-- Content -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  What do you want to remember?
                </label>
                <textarea
                  ref="contentTextarea"
                  v-model="content"
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Enter your memory content..."
                  @keydown.ctrl.enter="handleSave"
                  @keydown.meta.enter="handleSave"
                />
              </div>

              <!-- Type and Importance (side by side) -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Type
                  </label>
                  <select
                    v-model="memoryType"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option v-for="type in MEMORY_TYPES" :key="type" :value="type">
                      {{ type.charAt(0).toUpperCase() + type.slice(1) }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Importance: {{ importance }}
                  </label>
                  <input
                    v-model.number="importance"
                    type="range"
                    min="1"
                    max="100"
                    class="w-full accent-blue-600 mt-2"
                  />
                </div>
              </div>

              <!-- Tags with suggestions -->
              <div class="relative">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  v-model="tagsInput"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="tag1, tag2, tag3"
                  @focus="showSuggestions = true"
                  @blur="handleTagsBlur"
                />
                <!-- Tag suggestions dropdown -->
                <div
                  v-if="showSuggestions && tagSuggestions.length > 0"
                  class="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg"
                >
                  <button
                    v-for="tag in tagSuggestions"
                    :key="tag"
                    @mousedown.prevent="addSuggestion(tag)"
                    class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg"
                  >
                    {{ tag }}
                  </button>
                </div>
                <!-- Parsed tags preview -->
                <div v-if="parsedTags.length > 0" class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="tag in parsedTags"
                    :key="tag"
                    class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <input
                  v-model="keepOpen"
                  type="checkbox"
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
                Keep open after save
              </label>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-400">Ctrl+Enter to save</span>
                <button
                  @click="handleSave"
                  :disabled="!canSave"
                  class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
                  <Plus v-else class="w-4 h-4" />
                  {{ isSaving ? 'Saving...' : 'Create Memory' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
