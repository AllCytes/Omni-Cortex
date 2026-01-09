import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, Memory, MemoryStats, MemoryUpdate, FilterState, Activity, TimelineEntry, ProjectConfig } from '@/types'
import * as api from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const memories = ref<Memory[]>([])
  const selectedMemory = ref<Memory | null>(null)
  const stats = ref<MemoryStats | null>(null)
  const activities = ref<Activity[]>([])
  const timeline = ref<TimelineEntry[]>([])
  const tags = ref<Array<{ name: string; count: number }>>([])
  const projectConfig = ref<ProjectConfig | null>(null)

  const filters = ref<FilterState>({
    memory_type: null,
    status: null,
    tags: [],
    search: '',
    min_importance: null,
    max_importance: null,
    sort_by: 'last_accessed',
    sort_order: 'desc',
  })

  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isConnected = ref(false)
  const lastUpdated = ref<number | null>(null)

  // Pagination
  const page = ref(0)
  const pageSize = ref(50)
  const hasMore = ref(true)

  // Computed
  const currentDbPath = computed(() => currentProject.value?.db_path ?? '')

  // Actions
  async function loadProjects() {
    isLoading.value = true
    error.value = null
    try {
      projects.value = await api.getProjects()
      // Also load project config
      await loadProjectConfig()
      // Auto-select first project if none selected
      if (!currentProject.value && projects.value.length > 0) {
        await switchProject(projects.value[0])
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load projects'
      console.error('Failed to load projects:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function loadProjectConfig() {
    try {
      projectConfig.value = await api.getProjectConfig()
    } catch (e) {
      console.error('Failed to load project config:', e)
    }
  }

  async function switchProject(project: Project) {
    currentProject.value = project
    // Reset state
    memories.value = []
    selectedMemory.value = null
    page.value = 0
    hasMore.value = true
    // Load data for new project
    await Promise.all([
      loadMemories(true),
      loadStats(),
      loadTags(),
    ])
  }

  async function loadMemories(reset = false) {
    if (!currentDbPath.value) return

    if (reset) {
      page.value = 0
      hasMore.value = true
    }

    isLoading.value = true
    error.value = null

    try {
      const newMemories = await api.getMemories(
        currentDbPath.value,
        filters.value,
        pageSize.value,
        page.value * pageSize.value
      )

      if (reset) {
        memories.value = newMemories
      } else {
        memories.value = [...memories.value, ...newMemories]
      }

      hasMore.value = newMemories.length === pageSize.value
      lastUpdated.value = Date.now()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load memories'
      console.error('Failed to load memories:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function refresh() {
    await Promise.all([
      loadMemories(true),
      loadStats(),
      loadTags(),
    ])
  }

  async function loadMore() {
    if (!hasMore.value || isLoading.value) return
    page.value++
    await loadMemories(false)
  }

  async function loadStats() {
    if (!currentDbPath.value) return

    try {
      stats.value = await api.getMemoryStats(currentDbPath.value)
    } catch (e) {
      console.error('Failed to load stats:', e)
    }
  }

  async function loadTags() {
    if (!currentDbPath.value) return

    try {
      tags.value = await api.getTags(currentDbPath.value)
    } catch (e) {
      console.error('Failed to load tags:', e)
    }
  }

  async function loadActivities() {
    if (!currentDbPath.value) return

    try {
      activities.value = await api.getActivities(currentDbPath.value)
    } catch (e) {
      console.error('Failed to load activities:', e)
    }
  }

  async function loadTimeline(hours = 24) {
    if (!currentDbPath.value) return

    try {
      timeline.value = await api.getTimeline(currentDbPath.value, hours)
    } catch (e) {
      console.error('Failed to load timeline:', e)
    }
  }

  async function selectMemory(memory: Memory) {
    selectedMemory.value = memory
  }

  function clearSelection() {
    selectedMemory.value = null
  }

  function applyFilters(newFilters: Partial<FilterState>) {
    filters.value = { ...filters.value, ...newFilters }
    loadMemories(true)
  }

  function resetFilters() {
    filters.value = {
      memory_type: null,
      status: null,
      tags: [],
      search: '',
      min_importance: null,
      max_importance: null,
      sort_by: 'last_accessed',
      sort_order: 'desc',
    }
    loadMemories(true)
  }

  async function search(query: string) {
    if (!currentDbPath.value || !query.trim()) {
      applyFilters({ search: '' })
      return
    }

    applyFilters({ search: query })
  }

  async function updateMemory(memoryId: string, updates: MemoryUpdate): Promise<Memory | null> {
    if (!currentDbPath.value) return null

    try {
      const updated = await api.updateMemory(currentDbPath.value, memoryId, updates)
      handleMemoryUpdated(updated)
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update memory'
      console.error('Failed to update memory:', e)
      return null
    }
  }

  async function deleteMemoryById(memoryId: string): Promise<boolean> {
    if (!currentDbPath.value) return false

    try {
      await api.deleteMemory(currentDbPath.value, memoryId)
      handleMemoryDeleted(memoryId)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete memory'
      console.error('Failed to delete memory:', e)
      return false
    }
  }

  // WebSocket event handlers
  function handleMemoryCreated(memory: Memory) {
    memories.value = [memory, ...memories.value]
    if (stats.value) {
      stats.value.total_count++
    }
  }

  function handleMemoryUpdated(memory: Memory) {
    const index = memories.value.findIndex(m => m.id === memory.id)
    if (index !== -1) {
      memories.value[index] = memory
    }
    if (selectedMemory.value?.id === memory.id) {
      selectedMemory.value = memory
    }
  }

  function handleMemoryDeleted(memoryId: string) {
    memories.value = memories.value.filter(m => m.id !== memoryId)
    if (selectedMemory.value?.id === memoryId) {
      selectedMemory.value = null
    }
    if (stats.value) {
      stats.value.total_count--
    }
  }

  function handleDatabaseChanged() {
    // Reload data when database changes externally
    loadMemories(true)
    loadStats()
    loadTags()
  }

  function setConnected(connected: boolean) {
    isConnected.value = connected
  }

  return {
    // State
    projects,
    currentProject,
    projectConfig,
    memories,
    selectedMemory,
    stats,
    activities,
    timeline,
    tags,
    filters,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    hasMore,

    // Computed
    currentDbPath,

    // Actions
    loadProjects,
    loadProjectConfig,
    switchProject,
    loadMemories,
    loadMore,
    refresh,
    loadStats,
    loadTags,
    loadActivities,
    loadTimeline,
    selectMemory,
    clearSelection,
    applyFilters,
    resetFilters,
    search,
    updateMemory,
    deleteMemoryById,

    // WebSocket handlers
    handleMemoryCreated,
    handleMemoryUpdated,
    handleMemoryDeleted,
    handleDatabaseChanged,
    setConnected,
  }
})
