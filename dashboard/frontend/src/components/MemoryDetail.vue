<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Memory, MemoryUpdate } from '@/types'
import { TYPE_COLORS } from '@/types'
import { useDashboardStore } from '@/stores/dashboardStore'
import { X, Copy, Check, Download, FileJson, FileText, Pencil, Trash2, Loader2 } from 'lucide-vue-next'
import { exportToJson, exportToMarkdown, exportSingleMemoryToMarkdown, copyToClipboard } from '@/services/export'
import MemoryEditModal from './MemoryEditModal.vue'

const props = defineProps<{
  memory: Memory
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()
const isEditModalOpen = ref(false)
const isDeleting = ref(false)
const showDeleteConfirm = ref(false)

const copied = ref(false)
const copiedMarkdown = ref(false)

const typeColor = computed(() => TYPE_COLORS[props.memory.memory_type] || 'bg-gray-500')

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  const date = new Date(dateStr)
  return date.toLocaleString()
}

async function copyContent() {
  const success = await copyToClipboard(props.memory.content)
  if (success) {
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}

async function copyAsMarkdown() {
  const markdown = exportSingleMemoryToMarkdown(props.memory)
  const success = await copyToClipboard(markdown)
  if (success) {
    copiedMarkdown.value = true
    setTimeout(() => {
      copiedMarkdown.value = false
    }, 2000)
  }
}

function downloadJson() {
  exportToJson([props.memory], `memory-${props.memory.id}.json`)
}

function downloadMarkdown() {
  exportToMarkdown([props.memory], `memory-${props.memory.id}.md`)
}

function openEditModal() {
  isEditModalOpen.value = true
}

async function handleSaveEdit(updates: MemoryUpdate) {
  const result = await store.updateMemory(props.memory.id, updates)
  if (result) {
    isEditModalOpen.value = false
  }
}

async function handleDelete() {
  if (!showDeleteConfirm.value) {
    showDeleteConfirm.value = true
    return
  }

  isDeleting.value = true
  const success = await store.deleteMemoryById(props.memory.id)
  isDeleting.value = false

  if (success) {
    emit('close')
  }
  showDeleteConfirm.value = false
}

function cancelDelete() {
  showDeleteConfirm.value = false
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 h-[calc(100vh-280px)] flex flex-col">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-2">
        <span :class="['px-2 py-0.5 rounded-full text-xs font-medium text-white', typeColor]">
          {{ memory.memory_type }}
        </span>
        <span
          :class="[
            'px-2 py-0.5 rounded-full text-xs capitalize',
            memory.status === 'fresh' && 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
            memory.status === 'needs_review' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
            memory.status === 'outdated' && 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
            memory.status === 'archived' && 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
          ]"
        >
          {{ memory.status.replace('_', ' ') }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <!-- Edit Button -->
        <button
          @click="openEditModal"
          class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors text-blue-600 dark:text-blue-400"
          title="Edit memory"
        >
          <Pencil class="w-4 h-4" />
        </button>
        <!-- Delete Button -->
        <button
          v-if="!showDeleteConfirm"
          @click="handleDelete"
          class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors text-red-600 dark:text-red-400"
          title="Delete memory"
        >
          <Trash2 class="w-4 h-4" />
        </button>
        <!-- Delete Confirmation -->
        <div v-else class="flex items-center gap-1">
          <button
            @click="handleDelete"
            :disabled="isDeleting"
            class="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            <Loader2 v-if="isDeleting" class="w-3 h-3 animate-spin" />
            <span v-else>Confirm</span>
          </button>
          <button
            @click="cancelDelete"
            :disabled="isDeleting"
            class="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
        <!-- Close Button -->
        <button
          @click="emit('close')"
          class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-4">
      <!-- Main Content -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase">Content</h3>
          <div class="flex items-center gap-2">
            <button
              @click="copyContent"
              class="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              title="Copy content"
            >
              <Check v-if="copied" class="w-4 h-4" />
              <Copy v-else class="w-4 h-4" />
              {{ copied ? 'Copied!' : 'Copy' }}
            </button>
          </div>
        </div>
        <div class="memory-content bg-gray-50 dark:bg-gray-900 rounded-lg p-4 text-sm">
          {{ memory.content }}
        </div>
      </div>

      <!-- Context -->
      <div v-if="memory.context" class="mb-4">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Context</h3>
        <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 text-sm text-gray-600 dark:text-gray-400">
          {{ memory.context }}
        </div>
      </div>

      <!-- Tags -->
      <div v-if="memory.tags.length > 0" class="mb-4">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Tags</h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in memory.tags"
            :key="tag"
            class="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm"
          >
            {{ tag }}
          </span>
        </div>
      </div>

      <!-- Metadata -->
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div class="text-gray-500 dark:text-gray-400 mb-1">Importance</div>
          <div class="flex items-center gap-2">
            <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full', typeColor]"
                :style="{ width: `${memory.importance_score}%` }"
              ></div>
            </div>
            <span class="font-medium">{{ memory.importance_score }}</span>
          </div>
        </div>
        <div>
          <div class="text-gray-500 dark:text-gray-400 mb-1">Access Count</div>
          <div class="font-medium">{{ memory.access_count }} views</div>
        </div>
        <div>
          <div class="text-gray-500 dark:text-gray-400 mb-1">Created</div>
          <div class="font-medium">{{ formatDate(memory.created_at) }}</div>
        </div>
        <div>
          <div class="text-gray-500 dark:text-gray-400 mb-1">Last Accessed</div>
          <div class="font-medium">{{ formatDate(memory.last_accessed) }}</div>
        </div>
      </div>

      <!-- Export Options -->
      <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">Export</h3>
        <div class="flex flex-wrap gap-2">
          <button
            @click="copyAsMarkdown"
            class="flex items-center gap-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm transition-colors"
            title="Copy as Markdown"
          >
            <Check v-if="copiedMarkdown" class="w-4 h-4 text-green-600" />
            <FileText v-else class="w-4 h-4" />
            {{ copiedMarkdown ? 'Copied!' : 'Copy MD' }}
          </button>
          <button
            @click="downloadJson"
            class="flex items-center gap-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm transition-colors"
            title="Download as JSON"
          >
            <FileJson class="w-4 h-4" />
            JSON
          </button>
          <button
            @click="downloadMarkdown"
            class="flex items-center gap-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm transition-colors"
            title="Download as Markdown"
          >
            <Download class="w-4 h-4" />
            Markdown
          </button>
        </div>
      </div>

      <!-- ID -->
      <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div class="text-xs text-gray-500 dark:text-gray-400">
          ID: <span class="font-mono">{{ memory.id }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Edit Modal -->
  <MemoryEditModal
    :memory="memory"
    :is-open="isEditModalOpen"
    @close="isEditModalOpen = false"
    @save="handleSaveEdit"
  />
</template>
