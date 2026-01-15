<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { MessageSquare, BarChart3, HelpCircle, Zap, RefreshCw } from 'lucide-vue-next'

// Types for style profile data
interface StyleProfile {
  totalMessages: number
  avgWordCount: number
  primaryTone: string
  questionPercentage: number
  toneDistribution: Record<string, number>
  styleMarkers: string[]
}

const store = useDashboardStore()
const loading = ref(false)
const error = ref<string | null>(null)
const styleProfile = ref<StyleProfile | null>(null)

// Tone color mapping
const TONE_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  direct: { bg: 'bg-blue-500', text: 'text-blue-500', label: 'Direct' },
  polite: { bg: 'bg-green-500', text: 'text-green-500', label: 'Polite' },
  inquisitive: { bg: 'bg-purple-500', text: 'text-purple-500', label: 'Inquisitive' },
  technical: { bg: 'bg-orange-500', text: 'text-orange-500', label: 'Technical' },
  casual: { bg: 'bg-pink-500', text: 'text-pink-500', label: 'Casual' },
  urgent: { bg: 'bg-red-500', text: 'text-red-500', label: 'Urgent' },
}

// Computed properties
const toneData = computed(() => {
  if (!styleProfile.value?.toneDistribution) return []
  const total = Object.values(styleProfile.value.toneDistribution).reduce((a, b) => a + b, 0) || 1
  return Object.entries(styleProfile.value.toneDistribution)
    .map(([tone, count]) => ({
      tone,
      count,
      percentage: Math.round((count / total) * 100),
      color: TONE_COLORS[tone] || { bg: 'bg-gray-500', text: 'text-gray-500', label: tone }
    }))
    .sort((a, b) => b.count - a.count)
})

const primaryToneColor = computed(() => {
  if (!styleProfile.value?.primaryTone) return TONE_COLORS.direct
  return TONE_COLORS[styleProfile.value.primaryTone] || { bg: 'bg-gray-500', text: 'text-gray-500', label: styleProfile.value.primaryTone }
})

// Fetch style profile data from user_messages table
async function fetchStyleProfile() {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    const dbPath = store.currentProject.db_path
    const response = await fetch(`/api/style/profile?project=${encodeURIComponent(dbPath)}`)

    if (!response.ok) {
      // API doesn't exist yet - compute from local data or show placeholder
      await computeLocalStyleProfile()
      return
    }

    const data = await response.json()
    styleProfile.value = data
  } catch (e) {
    // Fallback to computing locally if API not available
    await computeLocalStyleProfile()
  } finally {
    loading.value = false
  }
}

// Compute style profile locally by querying user_messages
async function computeLocalStyleProfile() {
  if (!store.currentProject) {
    styleProfile.value = getDefaultProfile()
    return
  }

  try {
    const dbPath = store.currentProject.db_path
    // Try to get user messages data directly via a SQL endpoint or activities
    const response = await fetch(`/api/activities?project=${encodeURIComponent(dbPath)}&limit=500`)

    if (!response.ok) {
      styleProfile.value = getDefaultProfile()
      return
    }

    // For now, use placeholder data since user_messages API isn't implemented
    // This will be replaced when the API is added
    styleProfile.value = getDefaultProfile()
  } catch (e) {
    styleProfile.value = getDefaultProfile()
  }
}

function getDefaultProfile(): StyleProfile {
  return {
    totalMessages: 0,
    avgWordCount: 0,
    primaryTone: 'direct',
    questionPercentage: 0,
    toneDistribution: {},
    styleMarkers: ['No data available yet']
  }
}

// Watch for project changes
watch(() => store.currentProject, () => {
  fetchStyleProfile()
}, { immediate: true })

onMounted(() => {
  fetchStyleProfile()
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <MessageSquare class="w-5 h-5 text-indigo-500" />
        Style Profile
      </h2>
      <button
        @click="fetchStyleProfile"
        :disabled="loading"
        class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
        title="Refresh style data"
      >
        <RefreshCw :class="['w-4 h-4 text-gray-500', { 'animate-spin': loading }]" />
      </button>
    </div>

    <!-- Error State -->
    <div v-if="error" class="text-red-500 text-sm mb-4 p-2 bg-red-50 dark:bg-red-900/20 rounded">
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="loading && !styleProfile" class="animate-pulse space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <div class="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>

    <!-- Stats Content -->
    <div v-else-if="styleProfile" class="space-y-6">
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 gap-4">
        <!-- Total Messages -->
        <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <MessageSquare class="w-4 h-4" />
            Total Messages
          </div>
          <div class="text-2xl font-bold">
            {{ styleProfile.totalMessages.toLocaleString() }}
          </div>
        </div>

        <!-- Avg Words -->
        <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <BarChart3 class="w-4 h-4" />
            Avg Words
          </div>
          <div class="text-2xl font-bold">
            {{ styleProfile.avgWordCount.toFixed(1) }}
          </div>
        </div>

        <!-- Primary Tone -->
        <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <Zap class="w-4 h-4" />
            Primary Tone
          </div>
          <div class="flex items-center gap-2">
            <span :class="['w-3 h-3 rounded-full', primaryToneColor.bg]"></span>
            <span class="text-lg font-semibold capitalize">
              {{ primaryToneColor.label }}
            </span>
          </div>
        </div>

        <!-- Questions % -->
        <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <HelpCircle class="w-4 h-4" />
            Questions
          </div>
          <div class="text-2xl font-bold">
            {{ styleProfile.questionPercentage.toFixed(0) }}%
          </div>
        </div>
      </div>

      <!-- Tone Distribution Bar -->
      <div v-if="toneData.length > 0">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Tone Distribution
        </h3>

        <!-- Stacked Bar -->
        <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex">
          <div
            v-for="item in toneData"
            :key="item.tone"
            :class="['h-full transition-all', item.color.bg]"
            :style="{ width: `${item.percentage}%` }"
            :title="`${item.color.label}: ${item.percentage}%`"
          ></div>
        </div>

        <!-- Legend -->
        <div class="flex flex-wrap gap-3 mt-3">
          <div
            v-for="item in toneData"
            :key="item.tone"
            class="flex items-center gap-1.5 text-sm"
          >
            <span :class="['w-3 h-3 rounded-full', item.color.bg]"></span>
            <span class="text-gray-600 dark:text-gray-400">
              {{ item.color.label }}
            </span>
            <span class="text-gray-500 dark:text-gray-500">
              ({{ item.percentage }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- Empty Tone State -->
      <div v-else class="text-center py-4 text-gray-500 dark:text-gray-400">
        <p class="text-sm">No tone data available yet</p>
        <p class="text-xs mt-1">Start a conversation to begin tracking your communication style</p>
      </div>

      <!-- Key Style Markers -->
      <div v-if="styleProfile.styleMarkers.length > 0">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Key Style Markers
        </h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="(marker, index) in styleProfile.styleMarkers"
            :key="index"
            class="px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm"
          >
            {{ marker }}
          </span>
        </div>
      </div>
    </div>

    <!-- No Project Selected -->
    <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
      <MessageSquare class="w-12 h-12 mx-auto mb-3 opacity-50" />
      <p>Select a project to view style profile</p>
    </div>
  </div>
</template>
