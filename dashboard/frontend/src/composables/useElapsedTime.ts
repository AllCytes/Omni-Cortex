import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

/**
 * Composable for tracking elapsed time since a timestamp with auto-updating display.
 * Uses Page Visibility API to pause updates when tab is hidden for performance.
 */
export function useElapsedTime(timestampRef: () => number | null, updateIntervalMs = 1000) {
  const elapsed = ref(0)
  let intervalId: ReturnType<typeof setInterval> | null = null

  function formatElapsed(ms: number): string {
    if (ms < 5000) return 'Just now'
    if (ms < 60000) return `${Math.floor(ms / 1000)}s ago`
    if (ms < 3600000) return `${Math.floor(ms / 60000)}m ago`
    if (ms < 86400000) return `${Math.floor(ms / 3600000)}h ago`
    return new Date(Date.now() - ms).toLocaleString()
  }

  const formattedElapsed = computed(() => {
    const timestamp = timestampRef()
    if (!timestamp) return ''
    return formatElapsed(elapsed.value)
  })

  function updateElapsed() {
    const timestamp = timestampRef()
    if (timestamp) {
      elapsed.value = Date.now() - timestamp
    }
  }

  function startTimer() {
    if (intervalId) clearInterval(intervalId)
    updateElapsed() // Immediate update
    intervalId = setInterval(updateElapsed, updateIntervalMs)
  }

  function stopTimer() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  // Handle Page Visibility API for performance optimization
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

  // Restart timer when timestamp changes (e.g., new data loaded)
  watch(timestampRef, (newVal) => {
    if (newVal) {
      elapsed.value = Date.now() - newVal
    }
  })

  return { elapsed, formattedElapsed }
}
