<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Memory, MemoryUpdate } from '@/types'
import { MEMORY_TYPES, MEMORY_STATUSES } from '@/types'
import { X, Save, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  memory: Memory
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', updates: MemoryUpdate): void
}>()

const isSaving = ref(false)

// Form state
const content = ref('')
const context = ref('')
const memoryType = ref('')
const status = ref('')
const importance = ref(50)
const tagsInput = ref('')

// Initialize form when memory changes
watch(() => props.memory, (newMemory) => {
  if (newMemory) {
    content.value = newMemory.content
    context.value = newMemory.context || ''
    memoryType.value = newMemory.memory_type
    status.value = newMemory.status
    importance.value = newMemory.importance_score
    tagsInput.value = newMemory.tags.join(', ')
  }
}, { immediate: true })

// Reset form when modal opens
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && props.memory) {
    content.value = props.memory.content
    context.value = props.memory.context || ''
    memoryType.value = props.memory.memory_type
    status.value = props.memory.status
    importance.value = props.memory.importance_score
    tagsInput.value = props.memory.tags.join(', ')
  }
})

// const typeColor = computed(() => TYPE_COLORS[memoryType.value] || 'bg-gray-500') // TODO: add colored type badge

const parsedTags = computed(() => {
  if (!tagsInput.value.trim()) return []
  return tagsInput.value.split(',').map(t => t.trim()).filter(t => t.length > 0)
})

const hasChanges = computed(() => {
  if (!props.memory) return false
  return (
    content.value !== props.memory.content ||
    context.value !== (props.memory.context || '') ||
    memoryType.value !== props.memory.memory_type ||
    status.value !== props.memory.status ||
    importance.value !== props.memory.importance_score ||
    JSON.stringify(parsedTags.value) !== JSON.stringify(props.memory.tags)
  )
})

async function handleSave() {
  if (!hasChanges.value || isSaving.value) return

  isSaving.value = true

  const updates: MemoryUpdate = {}

  if (content.value !== props.memory.content) {
    updates.content = content.value
  }
  if (context.value !== (props.memory.context || '')) {
    updates.context = context.value || undefined
  }
  if (memoryType.value !== props.memory.memory_type) {
    updates.type = memoryType.value
  }
  if (status.value !== props.memory.status) {
    updates.status = status.value
  }
  if (importance.value !== props.memory.importance_score) {
    updates.importance_score = importance.value
  }
  if (JSON.stringify(parsedTags.value) !== JSON.stringify(props.memory.tags)) {
    updates.tags = parsedTags.value
  }

  emit('save', updates)
  isSaving.value = false
}

function handleClose() {
  if (!isSaving.value) {
    emit('close')
  }
}
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
            class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
          >
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h2 class="text-lg font-semibold">Edit Memory</h2>
              <button
                @click="handleClose"
                :disabled="isSaving"
                class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
              >
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Form -->
            <div class="flex-1 overflow-y-auto p-6 space-y-4">
              <!-- Content -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Content
                </label>
                <textarea
                  v-model="content"
                  rows="6"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Memory content..."
                />
              </div>

              <!-- Context -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Context (optional)
                </label>
                <textarea
                  v-model="context"
                  rows="3"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Additional context..."
                />
              </div>

              <!-- Type and Status -->
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
                      {{ type }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Status
                  </label>
                  <select
                    v-model="status"
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option v-for="s in MEMORY_STATUSES" :key="s" :value="s">
                      {{ s.replace('_', ' ') }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Importance -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Importance: {{ importance }}
                </label>
                <input
                  v-model.number="importance"
                  type="range"
                  min="1"
                  max="100"
                  class="w-full accent-blue-600"
                />
                <div class="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Low (1)</span>
                  <span>High (100)</span>
                </div>
              </div>

              <!-- Tags -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  v-model="tagsInput"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="tag1, tag2, tag3"
                />
                <div v-if="parsedTags.length > 0" class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="tag in parsedTags"
                    :key="tag"
                    class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full text-xs"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
              <button
                @click="handleClose"
                :disabled="isSaving"
                class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                @click="handleSave"
                :disabled="!hasChanges || isSaving"
                class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
                <Save v-else class="w-4 h-4" />
                {{ isSaving ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
