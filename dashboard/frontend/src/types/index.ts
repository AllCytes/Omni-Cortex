// Project types
export interface Project {
  name: string
  path: string
  db_path: string
  last_modified: string | null
  memory_count: number
  is_global: boolean
  is_favorite: boolean
  is_registered: boolean
  display_name: string | null
}

export interface ProjectConfig {
  scan_directories: string[]
  registered_count: number
  favorites_count: number
}

// Memory types
export interface Memory {
  id: string
  content: string
  context: string | null
  memory_type: string
  status: string
  importance_score: number
  access_count: number
  created_at: string
  last_accessed: string | null
  tags: string[]
}

export interface MemoryStats {
  total_count: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  avg_importance: number
  total_access_count: number
  tags: Array<{ name: string; count: number }>
}

export interface MemoryUpdate {
  content?: string
  context?: string
  type?: string
  status?: string
  importance_score?: number
  tags?: string[]
}

// Activity types
export interface Activity {
  id: string
  session_id: string | null
  event_type: string
  tool_name: string | null
  tool_input: string | null
  tool_output: string | null
  success: boolean
  error_message: string | null
  duration_ms: number | null
  file_path: string | null
  timestamp: string
}

// Session types
export interface Session {
  id: string
  project_path: string
  started_at: string
  ended_at: string | null
  summary: string | null
  activity_count: number
}

// Timeline types
export interface TimelineEntry {
  timestamp: string
  entry_type: 'memory' | 'activity'
  data: Record<string, unknown>
}

// Filter types
export interface FilterState {
  memory_type: string | null
  status: string | null
  tags: string[]
  search: string
  min_importance: number | null
  max_importance: number | null
  sort_by: 'created_at' | 'last_accessed' | 'importance_score' | 'access_count'
  sort_order: 'asc' | 'desc'
}

// WebSocket event types
export interface WSEvent {
  event_type: string
  data: Record<string, unknown>
  timestamp: string
}

// Memory type constants
export const MEMORY_TYPES = [
  'decision',
  'solution',
  'insight',
  'error',
  'context',
  'preference',
  'todo',
  'reference',
  'workflow',
  'api',
  'other',
] as const

export type MemoryType = typeof MEMORY_TYPES[number]

// Status constants
export const MEMORY_STATUSES = [
  'fresh',
  'needs_review',
  'outdated',
  'archived',
] as const

export type MemoryStatus = typeof MEMORY_STATUSES[number]

// Type color mapping
export const TYPE_COLORS: Record<string, string> = {
  decision: 'bg-type-decision',
  solution: 'bg-type-solution',
  insight: 'bg-type-insight',
  error: 'bg-type-error',
  context: 'bg-type-context',
  preference: 'bg-type-preference',
  todo: 'bg-type-todo',
  reference: 'bg-type-reference',
  workflow: 'bg-type-workflow',
  api: 'bg-type-api',
  other: 'bg-type-other',
}

export const TYPE_TEXT_COLORS: Record<string, string> = {
  decision: 'text-type-decision',
  solution: 'text-type-solution',
  insight: 'text-type-insight',
  error: 'text-type-error',
  context: 'text-type-context',
  preference: 'text-type-preference',
  todo: 'text-type-todo',
  reference: 'text-type-reference',
  workflow: 'text-type-workflow',
  api: 'text-type-api',
  other: 'text-type-other',
}

export const TYPE_BORDER_COLORS: Record<string, string> = {
  decision: 'border-l-type-decision',
  solution: 'border-l-type-solution',
  insight: 'border-l-type-insight',
  error: 'border-l-type-error',
  context: 'border-l-type-context',
  preference: 'border-l-type-preference',
  todo: 'border-l-type-todo',
  reference: 'border-l-type-reference',
  workflow: 'border-l-type-workflow',
  api: 'border-l-type-api',
  other: 'border-l-type-other',
}
