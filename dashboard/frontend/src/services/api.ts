import axios from 'axios'
import type { Project, Memory, MemoryStats, Activity, Session, TimelineEntry, FilterState } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Projects
export async function getProjects(): Promise<Project[]> {
  const response = await api.get<Project[]>('/projects')
  return response.data
}

// Memories
export async function getMemories(
  dbPath: string,
  filters: Partial<FilterState> = {},
  limit = 50,
  offset = 0
): Promise<Memory[]> {
  const params = new URLSearchParams({
    project: dbPath,
    limit: limit.toString(),
    offset: offset.toString(),
  })

  if (filters.memory_type) params.set('type', filters.memory_type)
  if (filters.status) params.set('status', filters.status)
  if (filters.tags?.length) params.set('tags', filters.tags.join(','))
  if (filters.search) params.set('search', filters.search)
  if (filters.min_importance !== null && filters.min_importance !== undefined) {
    params.set('min_importance', filters.min_importance.toString())
  }
  if (filters.max_importance !== null && filters.max_importance !== undefined) {
    params.set('max_importance', filters.max_importance.toString())
  }
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_order) params.set('sort_order', filters.sort_order)

  const response = await api.get<Memory[]>(`/memories?${params}`)
  return response.data
}

export async function getMemory(dbPath: string, memoryId: string): Promise<Memory> {
  const response = await api.get<Memory>(`/memories/${memoryId}?project=${encodeURIComponent(dbPath)}`)
  return response.data
}

export async function getMemoryStats(dbPath: string): Promise<MemoryStats> {
  const response = await api.get<MemoryStats>(`/memories/stats/summary?project=${encodeURIComponent(dbPath)}`)
  return response.data
}

export async function searchMemories(dbPath: string, query: string, limit = 20): Promise<Memory[]> {
  const response = await api.get<Memory[]>(`/search?project=${encodeURIComponent(dbPath)}&q=${encodeURIComponent(query)}&limit=${limit}`)
  return response.data
}

// Activities
export async function getActivities(
  dbPath: string,
  eventType?: string,
  toolName?: string,
  limit = 100,
  offset = 0
): Promise<Activity[]> {
  const params = new URLSearchParams({
    project: dbPath,
    limit: limit.toString(),
    offset: offset.toString(),
  })

  if (eventType) params.set('event_type', eventType)
  if (toolName) params.set('tool_name', toolName)

  const response = await api.get<Activity[]>(`/activities?${params}`)
  return response.data
}

// Timeline
export async function getTimeline(
  dbPath: string,
  hours = 24,
  includeMemories = true,
  includeActivities = true
): Promise<TimelineEntry[]> {
  const params = new URLSearchParams({
    project: dbPath,
    hours: hours.toString(),
    include_memories: includeMemories.toString(),
    include_activities: includeActivities.toString(),
  })

  const response = await api.get<TimelineEntry[]>(`/timeline?${params}`)
  return response.data
}

// Tags
export async function getTags(dbPath: string): Promise<Array<{ name: string; count: number }>> {
  const response = await api.get<Array<{ name: string; count: number }>>(`/tags?project=${encodeURIComponent(dbPath)}`)
  return response.data
}

// Types distribution
export async function getTypeDistribution(dbPath: string): Promise<Record<string, number>> {
  const response = await api.get<Record<string, number>>(`/types?project=${encodeURIComponent(dbPath)}`)
  return response.data
}

// Sessions
export async function getSessions(dbPath: string, limit = 20): Promise<Session[]> {
  const response = await api.get<Session[]>(`/sessions?project=${encodeURIComponent(dbPath)}&limit=${limit}`)
  return response.data
}

// Health check
export async function healthCheck(): Promise<{ status: string; websocket_connections: number }> {
  const response = await api.get('/health')
  return response.data
}
