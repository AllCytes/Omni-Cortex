<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  timestamp: string
  compact?: boolean
  showIcon?: boolean
}>()

const elapsed = ref(0)
let intervalId: ReturnType<typeof setInterval> | null = null

function formatElapsed(ms: number): string {
  if (ms < 5000) return 'Just now'
  if (ms < 60000) {
    const secs = Math.floor(ms / 1000)
    return `${secs}s ago`
  }
  if (ms < 3600000) {
    const mins = Math.floor(ms / 60000)
    const secs = Math.floor((ms % 60000) / 1000)
    return props.compact ? `${mins}m ago` : `${mins}m ${secs}s ago`
  }
  if (ms < 86400000) {
    const hours = Math.floor(ms / 3600000)
    const mins = Math.floor((ms % 3600000) / 60000)
    return props.compact ? `${hours}h ago` : `${hours}h ${mins}m ago`
  }
  const days = Math.floor(ms / 86400000)
  return `${days}d ago`
}

const formattedElapsed = computed(() => formatElapsed(elapsed.value))

function updateElapsed() {
  const ts = new Date(props.timestamp).getTime()
  if (!isNaN(ts)) {
    elapsed.value = Date.now() - ts
  }
}

function startTimer() {
  if (intervalId) clearInterval(intervalId)
  updateElapsed()
  intervalId = setInterval(updateElapsed, 1000)
}

function stopTimer() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

// Page Visibility API for performance
function handleVisibilityChange() {
  if (document.hidden) {
    stopTimer()
  } else {
    startTimer()
  }
}

onMounted(() => {
  startTimer()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  stopTimer()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})

watch(() => props.timestamp, () => {
  updateElapsed()
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1 font-mono tabular-nums',
      compact ? 'text-xs' : 'text-sm',
      'text-gray-500 dark:text-gray-400'
    ]"
  >
    <svg
      v-if="showIcon"
      class="w-3 h-3"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
    {{ formattedElapsed }}
  </span>
</template>
