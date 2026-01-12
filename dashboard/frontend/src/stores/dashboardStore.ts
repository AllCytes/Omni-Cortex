import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, Memory, MemoryStats, MemoryUpdate, FilterState, Activity, TimelineEntry, ProjectConfig } from '@/types'
import * as api from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const projects = ref<Project[]>([])
  const selectedProjects = ref<Project[]>([])
  const currentProject = computed(() => selectedProjects.value[0] || null)
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
  const selectedDbPaths = computed(() => selectedProjects.value.map(p => p.db_path))
  const isMultiProject = computed(() => selectedProjects.value.length > 1)

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
    selectedProjects.value = [project]
    // Reset state
    memories.value = []
    selectedMemory.value = null
    page.value = 0
    hasMore.value = true
    // Load data for new project
    await loadAggregateData()
  }

  function toggleProjectSelection(project: Project) {
    const index = selectedProjects.value.findIndex(p => p.db_path === project.db_path)
    if (index >= 0) {
      // Use filter for immutable array update (better reactivity)
      selectedProjects.value = selectedProjects.value.filter(p => p.db_path !== project.db_path)
    } else {
      // Use spread operator for immutable array update (better reactivity)
      selectedProjects.value = [...selectedProjects.value, project]
    }
    loadAggregateData()
  }

  function selectAllProjects() {
    selectedProjects.value = [...projects.value]
    loadAggregateData()
  }

  function clearProjectSelection() {
    selectedProjects.value = []
    memories.value = []
    stats.value = null
    tags.value = []
  }

  async function loadAggregateData() {
    if (selectedProjects.value.length === 0) {
      // Clear all arrays when no projects are selected
      memories.value = []
      stats.value = null
      tags.value = []
      return
    }

    page.value = 0
    hasMore.value = true

    await Promise.all([
      loadAggregateMemories(),
      loadAggregateStats(),
      loadAggregateTags(),
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

  async function loadAggregateMemories(reset = true) {
    if (selectedDbPaths.value.length === 0) return

    if (reset) {
      page.value = 0
      hasMore.value = true
    }

    isLoading.value = true
    error.value = null

    try {
      const newMemories = await api.getAggregateMemories(
        selectedDbPaths.value,
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
      console.error('Failed to load aggregate memories:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function loadAggregateStats() {
    if (selectedDbPaths.value.length === 0) return

    try {
      stats.value = await api.getAggregateStats(selectedDbPaths.value)
    } catch (e) {
      console.error('Failed to load aggregate stats:', e)
    }
  }

  async function loadAggregateTags() {
    if (selectedDbPaths.value.length === 0) return

    try {
      tags.value = await api.getAggregateTags(selectedDbPaths.value)
    } catch (e) {
      console.error('Failed to load aggregate tags:', e)
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

  async function createMemory(request: api.MemoryCreateRequest): Promise<Memory | null> {
    if (!currentDbPath.value) return null

    try {
      const created = await api.createMemory(currentDbPath.value, request)
      handleMemoryCreated(created)
      // Refresh tags to include any new ones
      await loadTags()
      return created
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create memory'
      console.error('Failed to create memory:', e)
      return null
    }
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

  // Live feed state (IndyDevDan pattern)
  const recentActivities = ref<Activity[]>([])
  const recentSessions = ref<Array<{ id: string; started_at: string; ended_at: string | null; activity_count: number; summary: string | null }>>([])
  const newActivityIds = ref<Set<string>>(new Set())  // For highlight animation
  const lastActivityTimestamp = ref<number>(0)

  // WebSocket event handlers
  function handleMemoryCreated(memory: Memory) {
    // Forced reactivity with spread (IndyDevDan pattern)
    memories.value = [memory, ...memories.value]
    if (stats.value) {
      stats.value = { ...stats.value, total_count: stats.value.total_count + 1 }
    }
    lastUpdated.value = Date.now()
  }

  function handleMemoryUpdated(memory: Memory) {
    const index = memories.value.findIndex(m => m.id === memory.id)
    if (index !== -1) {
      // Forced reactivity
      const updated = [...memories.value]
      updated[index] = memory
      memories.value = updated
    }
    if (selectedMemory.value?.id === memory.id) {
      selectedMemory.value = memory
    }
    lastUpdated.value = Date.now()
  }

  function handleMemoryDeleted(memoryId: string) {
    memories.value = memories.value.filter(m => m.id !== memoryId)
    if (selectedMemory.value?.id === memoryId) {
      selectedMemory.value = null
    }
    if (stats.value) {
      stats.value = { ...stats.value, total_count: stats.value.total_count - 1 }
    }
    lastUpdated.value = Date.now()
  }

  function handleDatabaseChanged() {
    // Reload data when database changes externally
    loadMemories(true)
    loadStats()
    loadTags()
    lastUpdated.value = Date.now()
  }

  // Live feed handlers (IndyDevDan pattern)
  function handleActivityLogged(data: { project: string; activity: Record<string, unknown> }) {
    // Only process if it's for our current project
    if (!currentDbPath.value || !data.project.includes(currentProject.value?.name || '')) {
      // Check if project path matches
      const normalizedCurrent = currentDbPath.value.replace(/\\/g, '/').toLowerCase()
      const normalizedData = data.project.replace(/\\/g, '/').toLowerCase()
      if (!normalizedData.includes(normalizedCurrent) && !normalizedCurrent.includes(normalizedData)) {
        return
      }
    }

    const activity = data.activity as unknown as Activity

    // Check if we already have this activity (dedup)
    const exists = recentActivities.value.some(a => a.id === activity.id)
    if (exists) return

    // Add to recent activities with forced reactivity (prepend, limit to 100)
    recentActivities.value = [activity, ...recentActivities.value].slice(0, 100)

    // Also update main activities array
    const mainExists = activities.value.some(a => a.id === activity.id)
    if (!mainExists) {
      activities.value = [activity, ...activities.value].slice(0, 200)
    }

    // Mark as new for highlight animation (clear after 3 seconds)
    newActivityIds.value = new Set([...newActivityIds.value, activity.id])
    setTimeout(() => {
      newActivityIds.value = new Set([...newActivityIds.value].filter(id => id !== activity.id))
    }, 3000)

    lastActivityTimestamp.value = Date.now()
    lastUpdated.value = Date.now()
  }

  function handleSessionUpdated(data: { project: string; session: Record<string, unknown> }) {
    // Only process if it's for our current project
    const normalizedCurrent = currentDbPath.value.replace(/\\/g, '/').toLowerCase()
    const normalizedData = data.project.replace(/\\/g, '/').toLowerCase()
    if (!normalizedData.includes(normalizedCurrent) && !normalizedCurrent.includes(normalizedData)) {
      return
    }

    const session = data.session as { id: string; started_at: string; ended_at: string | null; activity_count: number; summary: string | null }

    // Update or add session
    const index = recentSessions.value.findIndex(s => s.id === session.id)
    if (index !== -1) {
      const updated = [...recentSessions.value]
      updated[index] = session
      recentSessions.value = updated
    } else {
      recentSessions.value = [session, ...recentSessions.value].slice(0, 10)
    }

    lastUpdated.value = Date.now()
  }

  function handleStatsUpdated(data: { project: string; stats: Record<string, unknown> }) {
    const normalizedCurrent = currentDbPath.value.replace(/\\/g, '/').toLowerCase()
    const normalizedData = data.project.replace(/\\/g, '/').toLowerCase()
    if (!normalizedData.includes(normalizedCurrent) && !normalizedCurrent.includes(normalizedData)) {
      return
    }

    // Update stats with forced reactivity
    if (data.stats) {
      stats.value = data.stats as unknown as MemoryStats
    }

    lastUpdated.value = Date.now()
  }

  function setConnected(connected: boolean) {
    isConnected.value = connected
  }

  // Helper to check if activity is new (for animation)
  function isNewActivity(activityId: string): boolean {
    return newActivityIds.value.has(activityId)
  }

  return {
    // State
    projects,
    selectedProjects,
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

    // Live feed state (IndyDevDan pattern)
    recentActivities,
    recentSessions,
    newActivityIds,
    lastActivityTimestamp,

    // Computed
    currentDbPath,
    selectedDbPaths,
    isMultiProject,

    // Actions
    loadProjects,
    loadProjectConfig,
    switchProject,
    toggleProjectSelection,
    selectAllProjects,
    clearProjectSelection,
    loadAggregateData,
    loadMemories,
    loadMore,
    refresh,
    loadStats,
    loadTags,
    loadAggregateMemories,
    loadAggregateStats,
    loadAggregateTags,
    loadActivities,
    loadTimeline,
    selectMemory,
    clearSelection,
    applyFilters,
    resetFilters,
    search,
    createMemory,
    updateMemory,
    deleteMemoryById,

    // WebSocket handlers
    handleMemoryCreated,
    handleMemoryUpdated,
    handleMemoryDeleted,
    handleDatabaseChanged,
    setConnected,

    // Live feed handlers (IndyDevDan pattern)
    handleActivityLogged,
    handleSessionUpdated,
    handleStatsUpdated,
    isNewActivity,
  }
})
