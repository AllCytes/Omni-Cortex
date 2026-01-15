<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getStyleSamples } from '@/services/api'
import type { StyleSamples } from '@/types'
import { Zap, MessageSquare, FileText, RefreshCw } from 'lucide-vue-next'

const store = useDashboardStore()
const samples = ref<StyleSamples | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const currentProject = computed(() => store.currentProject)

// Category configuration
const categories = [
  {
    key: 'professional' as keyof StyleSamples,
    icon: FileText,
    label: 'Professional',
    description: 'Formal, structured messages',
    color: 'blue'
  },
  {
    key: 'casual' as keyof StyleSamples,
    icon: MessageSquare,
    label: 'Casual',
    description: 'Relaxed, conversational tone',
    color: 'green'
  },
  {
    key: 'technical' as keyof StyleSamples,
    icon: Zap,
    label: 'Technical',
    description: 'Code-focused, precise language',
    color: 'purple'
  },
  {
    key: 'creative' as keyof StyleSamples,
    icon: MessageSquare,
    label: 'Creative',
    description: 'Expressive, unique phrasing',
    color: 'pink'
  }
]

const colorClasses: Record<string, { border: string; bg: string; icon: string }> = {
  blue: {
    border: 'border-l-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    icon: 'text-blue-500'
  },
  green: {
    border: 'border-l-green-500',
    bg: 'bg-green-50 dark:bg-green-900/20',
    icon: 'text-green-500'
  },
  purple: {
    border: 'border-l-purple-500',
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    icon: 'text-purple-500'
  },
  pink: {
    border: 'border-l-pink-500',
    bg: 'bg-pink-50 dark:bg-pink-900/20',
    icon: 'text-pink-500'
  }
}

async function fetchSamples() {
  if (!currentProject.value?.db_path) return

  loading.value = true
  error.value = null

  try {
    samples.value = await getStyleSamples(currentProject.value.db_path, 3)
  } catch (e) {
    console.error('Failed to fetch style samples:', e)
    error.value = 'Failed to load sample messages'
    // Set empty samples as fallback
    samples.value = {
      professional: [],
      casual: [],
      technical: [],
      creative: []
    }
  } finally {
    loading.value = false
  }
}

function truncate(text: string, maxLength: number = 200): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

// Watch for project changes
watch(currentProject, () => {
  fetchSamples()
}, { immediate: true })

onMounted(() => {
  if (currentProject.value) {
    fetchSamples()
  }
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold">Sample Messages</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Representative examples of how you communicate
        </p>
      </div>
      <button
        @click="fetchSamples"
        :disabled="loading"
        class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
        title="Refresh samples"
      >
        <RefreshCw :class="['w-4 h-4 text-gray-500', { 'animate-spin': loading }]" />
      </button>
    </div>

    <!-- Error State -->
    <div v-if="error" class="text-red-500 text-sm mb-4 p-2 bg-red-50 dark:bg-red-900/20 rounded">
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="loading && !samples" class="animate-pulse">
      <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="space-y-3">
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
          <div class="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div class="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div v-else-if="samples" class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Category columns -->
      <div
        v-for="category in categories"
        :key="category.key"
        class="space-y-3"
      >
        <!-- Category Header -->
        <div class="flex items-center gap-2 pb-2 border-b border-gray-200 dark:border-gray-700">
          <component
            :is="category.icon"
            :class="['w-5 h-5', colorClasses[category.color].icon]"
          />
          <div>
            <h3 class="font-medium text-sm">{{ category.label }}</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ category.description }}</p>
          </div>
        </div>

        <!-- Sample Messages -->
        <div
          v-for="(sample, idx) in samples[category.key]"
          :key="idx"
          :class="[
            'p-3 rounded-lg border-l-2 text-sm',
            colorClasses[category.color].border,
            colorClasses[category.color].bg
          ]"
        >
          <p class="text-gray-700 dark:text-gray-300 italic">
            "{{ truncate(sample) }}"
          </p>
        </div>

        <!-- Empty State for Category -->
        <div
          v-if="!samples[category.key] || samples[category.key].length === 0"
          class="p-4 text-center text-gray-400 dark:text-gray-500 text-sm border border-dashed border-gray-300 dark:border-gray-600 rounded-lg"
        >
          No {{ category.label.toLowerCase() }} samples yet
        </div>
      </div>
    </div>

    <!-- No Project Selected -->
    <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
      <MessageSquare class="w-12 h-12 mx-auto mb-3 opacity-50" />
      <p>Select a project to view sample messages</p>
    </div>
  </div>
</template>
