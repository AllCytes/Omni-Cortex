import axios from 'axios'
import type { Project, Memory, MemoryStats, MemoryUpdate, Activity, Session, TimelineEntry, FilterState, ProjectConfig } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Projects
export async function getProjects(): Promise<Project[]> {
  const response = await api.get<Project[]>('/projects')
  return response.data
}

// Transform API memory response to normalize field names
// Backend returns 'type' but frontend expects 'memory_type'
function normalizeMemory(data: Record<string, unknown>): Memory {
  return {
    ...data,
    memory_type: (data.memory_type || data.type || 'other') as string,
  } as Memory
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

  const response = await api.get<Record<string, unknown>[]>(`/memories?${params}`)
  return response.data.map(normalizeMemory)
}

export async function getMemory(dbPath: string, memoryId: string): Promise<Memory> {
  const response = await api.get<Record<string, unknown>>(`/memories/${memoryId}?project=${encodeURIComponent(dbPath)}`)
  return normalizeMemory(response.data)
}

export async function getMemoryStats(dbPath: string): Promise<MemoryStats> {
  const response = await api.get<MemoryStats>(`/memories/stats/summary?project=${encodeURIComponent(dbPath)}`)
  return response.data
}

export async function searchMemories(dbPath: string, query: string, limit = 20): Promise<Memory[]> {
  const response = await api.get<Record<string, unknown>[]>(`/search?project=${encodeURIComponent(dbPath)}&q=${encodeURIComponent(query)}&limit=${limit}`)
  return response.data.map(normalizeMemory)
}

export async function updateMemory(dbPath: string, memoryId: string, updates: MemoryUpdate): Promise<Memory> {
  const response = await api.put<Record<string, unknown>>(`/memories/${memoryId}?project=${encodeURIComponent(dbPath)}`, updates)
  return normalizeMemory(response.data)
}

export async function deleteMemory(dbPath: string, memoryId: string): Promise<{ message: string; id: string }> {
  const response = await api.delete<{ message: string; id: string }>(`/memories/${memoryId}?project=${encodeURIComponent(dbPath)}`)
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

// Chat
export interface ChatSource {
  id: string
  type: string
  content_preview: string
  tags: string[]
}

export interface ChatResponse {
  answer: string
  sources: ChatSource[]
  error: string | null
}

export async function getChatStatus(_dbPath: string): Promise<{ available: boolean; message: string }> {
  const response = await api.get('/chat/status')
  return response.data
}

// AbortController for cancelling chat requests
let chatAbortController: AbortController | null = null

export function cancelChatRequest(): void {
  if (chatAbortController) {
    chatAbortController.abort()
    chatAbortController = null
  }
}

export async function askAboutMemories(
  dbPath: string,
  question: string,
  maxMemories: number = 10
): Promise<ChatResponse> {
  // Cancel any existing request
  cancelChatRequest()

  // Create new abort controller
  chatAbortController = new AbortController()

  try {
    const response = await api.post<ChatResponse>(
      `/chat?project=${encodeURIComponent(dbPath)}`,
      { question, max_memories: maxMemories },
      {
        timeout: 120000, // 2 minutes for AI responses
        signal: chatAbortController.signal,
      }
    )
    return response.data
  } catch (error) {
    if (axios.isCancel(error)) {
      throw new Error('Request cancelled')
    }
    // Provide more helpful error messages
    if (error instanceof Error) {
      if (error.message.includes('timeout')) {
        throw new Error('The AI is taking too long to respond. Please try a simpler question or try again later.')
      }
      if (error.message.includes('Network Error')) {
        throw new Error('Network error. Please check your connection and try again.')
      }
    }
    throw error
  } finally {
    chatAbortController = null
  }
}

// Streaming chat response using Server-Sent Events
export function streamChatResponse(
  dbPath: string,
  question: string,
  onChunk: (text: string) => void,
  onSources: (sources: ChatSource[]) => void,
  onDone: () => void,
  onError: (error: Error) => void
): () => void {
  const url = `/api/chat/stream?project=${encodeURIComponent(dbPath)}&question=${encodeURIComponent(question)}`

  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'sources':
          onSources(data.data)
          break
        case 'chunk':
          onChunk(data.data)
          break
        case 'done':
          eventSource.close()
          onDone()
          break
        case 'error':
          eventSource.close()
          onError(new Error(data.data || 'Stream error'))
          break
      }
    } catch (e) {
      console.error('Failed to parse SSE event:', e)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    onError(new Error('Stream connection failed'))
  }

  // Return cleanup function
  return () => eventSource.close()
}

// Save conversation as memory
export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ConversationSaveRequest {
  messages: ConversationMessage[]
  referenced_memory_ids?: string[]
  importance?: number
}

export interface ConversationSaveResponse {
  memory_id: string
  summary: string
}

export async function saveConversation(
  dbPath: string,
  conversation: ConversationSaveRequest
): Promise<ConversationSaveResponse> {
  const response = await api.post<ConversationSaveResponse>(
    `/chat/save?project=${encodeURIComponent(dbPath)}`,
    conversation,
    { timeout: 60000 }
  )
  return response.data
}

// --- Stats Endpoints for Charts ---

export interface ActivityHeatmapEntry {
  date: string
  count: number
}

export interface ToolUsageEntry {
  tool_name: string
  count: number
  success_rate: number
}

export interface MemoryGrowthEntry {
  date: string
  count: number
  cumulative: number
}

export async function getActivityHeatmap(
  dbPath: string,
  days: number = 90
): Promise<ActivityHeatmapEntry[]> {
  const response = await api.get<ActivityHeatmapEntry[]>(
    `/stats/activity-heatmap?project=${encodeURIComponent(dbPath)}&days=${days}`
  )
  return response.data
}

export async function getToolUsage(
  dbPath: string,
  limit: number = 10
): Promise<ToolUsageEntry[]> {
  const response = await api.get<ToolUsageEntry[]>(
    `/stats/tool-usage?project=${encodeURIComponent(dbPath)}&limit=${limit}`
  )
  return response.data
}

export async function getMemoryGrowth(
  dbPath: string,
  days: number = 30
): Promise<MemoryGrowthEntry[]> {
  const response = await api.get<MemoryGrowthEntry[]>(
    `/stats/memory-growth?project=${encodeURIComponent(dbPath)}&days=${days}`
  )
  return response.data
}

// --- Session Context ---

export interface RecentSession {
  id: string
  project_path: string
  started_at: string
  ended_at: string | null
  summary: string | null
  activity_count: number
}

export async function getRecentSessions(
  dbPath: string,
  limit: number = 5
): Promise<RecentSession[]> {
  const response = await api.get<RecentSession[]>(
    `/sessions/recent?project=${encodeURIComponent(dbPath)}&limit=${limit}`
  )
  return response.data
}

// --- Freshness Review ---

export async function getMemoriesNeedingReview(
  dbPath: string,
  daysThreshold: number = 30,
  limit: number = 50
): Promise<Memory[]> {
  const response = await api.get<Record<string, unknown>[]>(
    `/memories/needs-review?project=${encodeURIComponent(dbPath)}&days_threshold=${daysThreshold}&limit=${limit}`
  )
  return response.data.map(normalizeMemory)
}

export async function bulkUpdateMemoryStatus(
  dbPath: string,
  memoryIds: string[],
  status: string
): Promise<{ updated_count: number; status: string }> {
  const response = await api.post<{ updated_count: number; status: string }>(
    `/memories/bulk-update-status?project=${encodeURIComponent(dbPath)}&status=${status}`,
    memoryIds
  )
  return response.data
}

// --- Relationship Graph ---

export interface GraphNode {
  id: string
  content: string
  type: string
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  strength: number
}

export interface RelationshipGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export async function getRelationshipGraph(
  dbPath: string,
  centerId?: string,
  depth: number = 2
): Promise<RelationshipGraph> {
  let url = `/relationships/graph?project=${encodeURIComponent(dbPath)}&depth=${depth}`
  if (centerId) {
    url += `&center_id=${encodeURIComponent(centerId)}`
  }
  const response = await api.get<RelationshipGraph>(url)
  return response.data
}

// --- Project Management ---

export async function getProjectConfig(): Promise<ProjectConfig> {
  const response = await api.get<ProjectConfig>('/projects/config')
  return response.data
}

export async function registerProject(path: string, displayName?: string): Promise<void> {
  await api.post('/projects/register', { path, display_name: displayName })
}

export async function unregisterProject(path: string): Promise<void> {
  await api.delete('/projects/register', { params: { path } })
}

export async function toggleFavorite(path: string): Promise<boolean> {
  const response = await api.post<{ is_favorite: boolean }>(
    '/projects/favorite',
    null,
    { params: { path } }
  )
  return response.data.is_favorite
}

export async function addScanDirectory(directory: string): Promise<void> {
  await api.post('/projects/scan-directories', null, { params: { directory } })
}

export async function removeScanDirectory(directory: string): Promise<void> {
  await api.delete('/projects/scan-directories', { params: { directory } })
}

export async function refreshProjects(): Promise<number> {
  const response = await api.post<{ count: number }>('/projects/refresh')
  return response.data.count
}
