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
  // Command analytics fields
  command_name: string | null
  command_scope: string | null
  mcp_server: string | null
  skill_name: string | null
  // Natural language summary fields
  summary: string | null
  summary_detail: string | null
}

// Activity detail (with full input/output)
export interface ActivityDetail extends Activity {
  tool_input_full: string | null
  tool_output_full: string | null
}

// Command usage analytics
export interface CommandUsageEntry {
  command_name: string
  command_scope: 'universal' | 'project' | 'unknown'
  count: number
  success_rate: number
  avg_duration_ms: number | null
}

// Skill usage analytics
export interface SkillUsageEntry {
  skill_name: string
  skill_scope: 'universal' | 'project' | 'unknown'
  count: number
  success_rate: number
  avg_duration_ms: number | null
}

// MCP usage analytics
export interface MCPUsageEntry {
  mcp_server: string
  tool_count: number
  total_calls: number
  success_rate: number
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

// === Style Tab Types ===

// User message tracking types
export interface UserMessage {
  id: string
  content: string
  tone: string | null
  word_count: number
  char_count: number
  created_at: string
  session_id: string | null
}

export interface UserMessageFilters {
  tone?: string
  search?: string
  min_word_count?: number
  max_word_count?: number
  since?: string
  until?: string
}

export interface UserMessagesResponse {
  messages: UserMessage[]
  total_count: number
  has_more: boolean
}

// Style profile types
export interface StyleProfile {
  total_messages: number
  avg_word_count: number
  avg_char_count: number
  tone_distribution: Record<string, number>
  vocabulary_richness: number
  common_phrases: string[]
  writing_patterns: {
    avg_sentence_length: number
    question_frequency: number
    exclamation_frequency: number
    formality_score: number
  }
}

export interface StyleSamples {
  professional: string[]
  casual: string[]
  technical: string[]
  creative: string[]
}

// Tone type constants
export const TONE_TYPES = [
  'professional',
  'casual',
  'technical',
  'creative',
  'formal',
  'friendly',
  'urgent',
  'neutral',
] as const

export type ToneType = typeof TONE_TYPES[number]

// Tone color mapping for UI
export const TONE_COLORS: Record<string, string> = {
  professional: 'bg-blue-500',
  casual: 'bg-green-500',
  technical: 'bg-purple-500',
  creative: 'bg-pink-500',
  formal: 'bg-slate-500',
  friendly: 'bg-amber-500',
  urgent: 'bg-red-500',
  neutral: 'bg-gray-500',
}

export const TONE_TEXT_COLORS: Record<string, string> = {
  professional: 'text-blue-500',
  casual: 'text-green-500',
  technical: 'text-purple-500',
  creative: 'text-pink-500',
  formal: 'text-slate-500',
  friendly: 'text-amber-500',
  urgent: 'text-red-500',
  neutral: 'text-gray-500',
}

// === Response Composer Types ===

export type ContextType = 'skool_post' | 'dm' | 'email' | 'comment' | 'general'
export type ResponseTemplate = 'answer' | 'guide' | 'redirect' | 'acknowledge'

export interface ComposeRequest {
  incoming_message: string
  context_type: ContextType
  template?: ResponseTemplate
  tone_level: number
  include_memories: boolean
}

export interface ComposedResponse {
  id: string
  response: string
  sources: ChatSource[]
  style_applied: boolean
  tone_level: number
  template_used?: ResponseTemplate
  incoming_message: string
  context_type: ContextType
  created_at: string
}

export interface ChatSource {
  id: string
  type: string
  content_preview: string
  tags: string[]
  project_path?: string
  project_name?: string
}
