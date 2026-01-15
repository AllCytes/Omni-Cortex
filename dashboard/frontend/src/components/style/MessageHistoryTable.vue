<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getUserMessages, deleteUserMessage } from '@/services/api'
import type { UserMessage, UserMessageFilters } from '@/types'
import { TONE_COLORS } from '@/types'
import { Search, Trash2, ChevronDown, ChevronUp, HelpCircle, Code, Terminal, Filter } from 'lucide-vue-next'
import LiveElapsedTime from '@/components/LiveElapsedTime.vue'

const store = useDashboardStore()
const messages = ref<UserMessage[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const expandedId = ref<string | null>(null)
const searchQuery = ref('')
const selectedTone = ref<string | null>(null)
const showFilters = ref(false)

const currentProject = computed(() => store.currentProject)

async function loadMessages() {
  if (!currentProject.value) return

  loading.value = true
  try {
    const result = await getUserMessages(currentProject.value, {
      limit: pageSize,
      offset: (page.value - 1) * pageSize,
      search: searchQuery.value || undefined,
      tone: selectedTone.value || undefined,
    })
    messages.value = result.messages
    total.value = result.total
  } catch (e) {
    console.error('Failed to load messages:', e)
  } finally {
    loading.value = false
  }
}

async function handleDelete(messageId: string) {
  if (!currentProject.value) return
  if (!confirm('Delete this message?')) return

  try {
    await deleteUserMessage(currentProject.value, messageId)
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
const totalPages = computed(() => Math.ceil(total.value / pageSize))

function prevPage() {
  if (page.value > 1) page.value--
}

function nextPage() {
  if (page.value < totalPages.value) page.value++
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
        <span class="text-sm text-gray-500">{{ total }} messages</span>
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
            v-for="tone in ['direct', 'polite', 'technical', 'inquisitive', 'casual', 'urgent']"
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
            <th class="px-4 py-3 text-left font-medium">Tone</th>
            <th class="px-4 py-3 text-center font-medium">Flags</th>
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
                <LiveElapsedTime :timestamp="msg.timestamp" />
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
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="tone in msg.tone_indicators"
                    :key="tone"
                    :class="['px-2 py-0.5 rounded-full text-xs capitalize', TONE_COLORS[tone] || 'bg-gray-200 dark:bg-gray-600']"
                  >
                    {{ tone }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-center gap-2">
                  <HelpCircle
                    v-if="msg.has_questions"
                    class="w-4 h-4 text-amber-500"
                    title="Contains questions"
                  />
                  <Code
                    v-if="msg.has_code_blocks"
                    class="w-4 h-4 text-blue-500"
                    title="Contains code"
                  />
                  <Terminal
                    v-if="msg.has_commands"
                    class="w-4 h-4 text-green-500"
                    title="Slash command"
                  />
                </div>
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
              </td>
            </tr>
          </template>

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
