<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getUserMessages, deleteUserMessage } from '@/services/api'
import type { UserMessage } from '@/types'
import { TONE_COLORS } from '@/types'
import { Search, Trash2, ChevronDown, ChevronUp, Filter, RefreshCw } from 'lucide-vue-next'
import LiveElapsedTime from '@/components/LiveElapsedTime.vue'

const store = useDashboardStore()
const messages = ref<UserMessage[]>([])
const totalCount = ref(0)
const hasMore = ref(false)
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const expandedId = ref<string | null>(null)
const searchQuery = ref('')
const selectedTone = ref<string | null>(null)
const showFilters = ref(false)

const currentProject = computed(() => store.currentProject)

async function loadMessages() {
  if (!currentProject.value?.db_path) return

  loading.value = true
  try {
    const result = await getUserMessages(
      currentProject.value.db_path,
      {
        search: searchQuery.value || undefined,
        tone: selectedTone.value || undefined,
      },
      pageSize,
      (page.value - 1) * pageSize
    )
    messages.value = result.messages
    totalCount.value = result.total_count
    hasMore.value = result.has_more
  } catch (e) {
    console.error('Failed to load messages:', e)
    // Set empty state on error
    messages.value = []
    totalCount.value = 0
    hasMore.value = false
  } finally {
    loading.value = false
  }
}

async function handleDelete(messageId: string) {
  if (!currentProject.value?.db_path) return
  if (!confirm('Delete this message?')) return

  try {
    await deleteUserMessage(currentProject.value.db_path, messageId)
    await loadMessages()
  } catch (e) {
    console.error('Failed to delete message:', e)
  }
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function truncate(text: string, length: number = 80): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

// Pagination
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize))

function prevPage() {
  if (page.value > 1) page.value--
}

function nextPage() {
  if (page.value < totalPages.value) page.value++
}

// Get tone badge class
function getToneBadgeClass(tone: string | null): string {
  if (!tone) return 'bg-gray-200 dark:bg-gray-600'
  return TONE_COLORS[tone] || 'bg-gray-200 dark:bg-gray-600'
}

// Watch for filter changes
watch([page, searchQuery, selectedTone], () => {
  loadMessages()
})

watch(currentProject, () => {
  page.value = 1
  loadMessages()
})

onMounted(() => {
  loadMessages()
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold">Message History</h3>
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-500">{{ totalCount }} messages</span>
          <button
            @click="loadMessages"
            :disabled="loading"
            class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            title="Refresh messages"
          >
            <RefreshCw :class="['w-4 h-4 text-gray-500', { 'animate-spin': loading }]" />
          </button>
        </div>
      </div>

      <!-- Search & Filter Bar -->
      <div class="flex gap-3">
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search messages..."
            class="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg border-0 focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          @click="showFilters = !showFilters"
          :class="[
            'px-3 py-2 rounded-lg flex items-center gap-2 transition-colors',
            showFilters ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600' : 'bg-gray-100 dark:bg-gray-700'
          ]"
        >
          <Filter class="w-4 h-4" />
          Filters
        </button>
      </div>

      <!-- Filter Panel (collapsible) -->
      <div v-if="showFilters" class="mt-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tone in ['professional', 'casual', 'technical', 'creative', 'formal', 'friendly', 'urgent', 'neutral']"
            :key="tone"
            @click="selectedTone = selectedTone === tone ? null : tone"
            :class="[
              'px-3 py-1 rounded-full text-sm capitalize transition-colors',
              selectedTone === tone
                ? 'bg-indigo-500 text-white'
                : 'bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500'
            ]"
          >
            {{ tone }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-700/50 text-sm">
          <tr>
            <th class="px-4 py-3 text-left font-medium">Time</th>
            <th class="px-4 py-3 text-left font-medium">Message</th>
            <th class="px-4 py-3 text-center font-medium">Words</th>
            <th class="px-4 py-3 text-center font-medium">Chars</th>
            <th class="px-4 py-3 text-left font-medium">Tone</th>
            <th class="px-4 py-3 text-center font-medium">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <template v-for="msg in messages" :key="msg.id">
            <!-- Main Row -->
            <tr
              class="hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer"
              @click="toggleExpand(msg.id)"
            >
              <td class="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                <LiveElapsedTime :timestamp="msg.created_at" />
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <component
                    :is="expandedId === msg.id ? ChevronUp : ChevronDown"
                    class="w-4 h-4 text-gray-400 flex-shrink-0"
                  />
                  <span class="text-sm">{{ truncate(msg.content) }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-center text-sm">{{ msg.word_count }}</td>
              <td class="px-4 py-3 text-center text-sm text-gray-500">{{ msg.char_count }}</td>
              <td class="px-4 py-3">
                <span
                  v-if="msg.tone"
                  :class="['px-2 py-0.5 rounded-full text-xs capitalize text-white', getToneBadgeClass(msg.tone)]"
                >
                  {{ msg.tone }}
                </span>
                <span v-else class="text-gray-400 text-xs">-</span>
              </td>
              <td class="px-4 py-3 text-center">
                <button
                  @click.stop="handleDelete(msg.id)"
                  class="p-1.5 text-gray-400 hover:text-red-500 rounded transition-colors"
                  title="Delete message"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </td>
            </tr>

            <!-- Expanded Content -->
            <tr v-if="expandedId === msg.id">
              <td colspan="6" class="px-4 py-4 bg-gray-50 dark:bg-gray-700/30">
                <div class="text-sm whitespace-pre-wrap font-mono bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
                  {{ msg.content }}
                </div>
                <div class="mt-2 text-xs text-gray-500 flex gap-4">
                  <span>Session: {{ msg.session_id || 'N/A' }}</span>
                </div>
              </td>
            </tr>
          </template>

          <!-- Loading State -->
          <tr v-if="loading && messages.length === 0">
            <td colspan="6" class="px-4 py-8 text-center">
              <RefreshCw class="w-6 h-6 animate-spin mx-auto text-gray-400" />
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="!loading && messages.length === 0">
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">
              No messages found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <span class="text-sm text-gray-500">
        Page {{ page }} of {{ totalPages }}
      </span>
      <div class="flex gap-2">
        <button
          @click="prevPage"
          :disabled="page === 1"
          class="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <button
          @click="nextPage"
          :disabled="page === totalPages"
          class="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>
