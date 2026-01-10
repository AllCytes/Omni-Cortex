<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import {
  askAboutMemories,
  getChatStatus,
  cancelChatRequest,
  streamChatResponse,
  saveConversation,
  type ChatSource,
} from '@/services/api'
import {
  Send,
  Loader2,
  MessageCircle,
  AlertCircle,
  Bot,
  User,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  X,
  Copy,
  Check,
  RefreshCw,
  Pencil,
  Bookmark,
  Download,
  Search,
  Keyboard,
  ChevronUp,
  FileText,
  FileJson,
  Clipboard,
  Image,
} from 'lucide-vue-next'
import ImageGenerationPanel from './ImageGenerationPanel.vue'
import { marked } from 'marked'
import SourceTooltip from './SourceTooltip.vue'
import { sanitizeMarkdown } from '@/utils/sanitize'
import { logger } from '@/utils/logger'

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true,
})

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
  timestamp: Date
  error?: boolean
  sourcesExpanded?: boolean
  copiedRecently?: boolean
  isEditing?: boolean
  editContent?: string
  isStreaming?: boolean
}

const store = useDashboardStore()
const messages = ref<Message[]>([])
const inputValue = ref('')
const isLoading = ref(false)
const isStreaming = ref(false)
const isChatAvailable = ref(false)
const chatUnavailableMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const elapsedTime = ref(0)
let elapsedTimer: ReturnType<typeof setInterval> | null = null
let streamCleanup: (() => void) | null = null

// Tooltip state
const hoveredSource = ref<ChatSource | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })
let hoverTimeout: ReturnType<typeof setTimeout> | null = null

// Save conversation state
const isSaving = ref(false)
const isSaved = ref(false)
const savedMemoryId = ref<string | null>(null)

// Export menu
const showExportMenu = ref(false)

// Search state
const showSearch = ref(false)
const searchQuery = ref('')
const searchResults = ref<number[]>([])
const currentSearchIndex = ref(0)

// Keyboard shortcuts help
const showShortcutsHelp = ref(false)

// Mode toggle: 'chat' or 'image'
const mode = ref<'chat' | 'image'>('chat')

// Type colors for source badges
const TYPE_COLORS: Record<string, string> = {
  decision: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  solution: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  fact: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  preference: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  progress: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  conversation: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  troubleshooting: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  other: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
}

// Suggested prompts
const suggestedPrompts = [
  'What decisions have I made about authentication?',
  'Summarize my recent solutions',
  'What errors have I encountered with Vue?',
  'Show me patterns I use frequently',
  'What are my coding preferences?',
]

// Character count
const charCount = computed(() => inputValue.value.length)
const maxChars = 4000

onMounted(async () => {
  await checkChatStatus()
  document.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  stopElapsedTimer()
  cancelChatRequest()
  if (streamCleanup) streamCleanup()
  document.removeEventListener('keydown', handleGlobalKeyDown)
})

// Watch for project changes to reset saved state
watch(() => store.currentDbPath, () => {
  isSaved.value = false
  savedMemoryId.value = null
})

function startElapsedTimer() {
  elapsedTime.value = 0
  elapsedTimer = setInterval(() => {
    elapsedTime.value++
  }, 1000)
}

function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
  elapsedTime.value = 0
}

function handleCancel() {
  cancelChatRequest()
  if (streamCleanup) {
    streamCleanup()
    streamCleanup = null
  }
  stopElapsedTimer()
  isLoading.value = false
  isStreaming.value = false

  // If there's a streaming message, mark it as cancelled
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage?.isStreaming) {
    lastMessage.isStreaming = false
    lastMessage.content += '\n\n*[Cancelled]*'
  } else {
    const cancelMessage: Message = {
      id: `msg_${Date.now()}_cancelled`,
      role: 'assistant',
      content: 'Request cancelled.',
      timestamp: new Date(),
      error: false,
    }
    messages.value.push(cancelMessage)
  }
  scrollToBottom()
}

async function checkChatStatus() {
  if (!store.currentDbPath) return
  try {
    const status = await getChatStatus(store.currentDbPath)
    isChatAvailable.value = status.available
    chatUnavailableMessage.value = status.message
  } catch (e) {
    isChatAvailable.value = false
    chatUnavailableMessage.value = 'Failed to check chat status'
  }
}

async function sendMessage() {
  if (!inputValue.value.trim() || isLoading.value || !store.currentDbPath) return

  const question = inputValue.value.trim()
  inputValue.value = ''
  isSaved.value = false
  savedMemoryId.value = null

  // Add user message
  const userMessage: Message = {
    id: `msg_${Date.now()}_user`,
    role: 'user',
    content: question,
    timestamp: new Date(),
  }
  messages.value.push(userMessage)
  scrollToBottom()

  // Use streaming if available
  await sendMessageStreaming(question)
}

async function sendMessageStreaming(question: string) {
  isLoading.value = true
  isStreaming.value = true
  startElapsedTimer()

  // Add placeholder assistant message
  const assistantMessage: Message = {
    id: `msg_${Date.now()}_assistant`,
    role: 'assistant',
    content: '',
    timestamp: new Date(),
    isStreaming: true,
    sourcesExpanded: false,
  }
  messages.value.push(assistantMessage)

  try {
    streamCleanup = streamChatResponse(
      store.currentDbPath!,
      question,
      (chunk) => {
        // Append chunk to streaming content
        assistantMessage.content += chunk
        scrollToBottom()
      },
      (sources) => {
        assistantMessage.sources = sources
      },
      () => {
        assistantMessage.isStreaming = false
        isStreaming.value = false
        isLoading.value = false
        stopElapsedTimer()
        streamCleanup = null
      },
      (error) => {
        assistantMessage.content = error.message
        assistantMessage.error = true
        assistantMessage.isStreaming = false
        isStreaming.value = false
        isLoading.value = false
        stopElapsedTimer()
        streamCleanup = null
      }
    )
  } catch (e) {
    // Fallback to non-streaming
    await sendMessageNonStreaming(question, assistantMessage)
  }
}

async function sendMessageNonStreaming(question: string, assistantMessage: Message) {
  try {
    const response = await askAboutMemories(store.currentDbPath!, question)

    assistantMessage.content = response.answer
    assistantMessage.sources = response.sources
    assistantMessage.error = !!response.error
    assistantMessage.isStreaming = false
  } catch (e) {
    if (e instanceof Error && e.message === 'Request cancelled') {
      return
    }
    assistantMessage.content = e instanceof Error ? e.message : 'Failed to get response'
    assistantMessage.error = true
    assistantMessage.isStreaming = false
  } finally {
    stopElapsedTimer()
    isLoading.value = false
    isStreaming.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function handleGlobalKeyDown(event: KeyboardEvent) {
  // Escape: Cancel or close modals
  if (event.key === 'Escape') {
    if (showShortcutsHelp.value) {
      showShortcutsHelp.value = false
      return
    }
    if (showSearch.value) {
      showSearch.value = false
      searchQuery.value = ''
      return
    }
    if (isLoading.value || isStreaming.value) {
      handleCancel()
      return
    }
  }

  // Ctrl/Cmd + / : Show shortcuts help
  if ((event.ctrlKey || event.metaKey) && event.key === '/') {
    event.preventDefault()
    showShortcutsHelp.value = !showShortcutsHelp.value
    return
  }

  // Ctrl/Cmd + F: Search in chat
  if ((event.ctrlKey || event.metaKey) && event.key === 'f' && messages.value.length > 0) {
    event.preventDefault()
    showSearch.value = true
    nextTick(() => {
      const searchInput = document.getElementById('chat-search-input')
      searchInput?.focus()
    })
    return
  }

  // Up arrow with empty input: Edit last message
  if (event.key === 'ArrowUp' && inputRef.value) {
    const input = inputRef.value
    if (input.value === '' && input.selectionStart === 0) {
      const lastUserMessageIndex = getLastUserMessageIndex()
      if (lastUserMessageIndex >= 0) {
        event.preventDefault()
        startEditMessage(messages.value[lastUserMessageIndex])
      }
    }
  }
}

// Parse markdown and convert [[Memory N]] references to clickable links
function renderMarkdown(content: string, sources?: ChatSource[]): string {
  // Parse memory references
  let processed = content.replace(/\[\[Memory (\d+)\]\]/g, (match, num) => {
    const idx = parseInt(num) - 1
    if (sources && sources[idx]) {
      return `<a href="#" class="memory-ref text-blue-600 dark:text-blue-400 hover:underline font-medium" data-memory-index="${idx}">[Memory ${num}]</a>`
    }
    return match
  })

  const rawHtml = marked.parse(processed) as string
  return sanitizeMarkdown(rawHtml)
}

function handleContentClick(event: MouseEvent, sources?: ChatSource[]) {
  const target = event.target as HTMLElement
  if (target.classList.contains('memory-ref')) {
    event.preventDefault()
    const index = parseInt(target.dataset.memoryIndex || '0')
    if (sources && sources[index]) {
      selectMemory(sources[index])
    }
  }
}

function toggleSources(message: Message) {
  message.sourcesExpanded = !message.sourcesExpanded
}

async function copyMessage(message: Message) {
  try {
    await navigator.clipboard.writeText(message.content)
    message.copiedRecently = true
    setTimeout(() => {
      message.copiedRecently = false
    }, 2000)
  } catch (e) {
    logger.error('Failed to copy:', e)
  }
}

async function regenerateResponse(userMessageIndex: number) {
  const userMessage = messages.value[userMessageIndex]
  if (!userMessage || userMessage.role !== 'user') return

  messages.value = messages.value.slice(0, userMessageIndex + 1)
  isSaved.value = false
  savedMemoryId.value = null

  await sendMessageStreaming(userMessage.content)
}

function startEditMessage(message: Message) {
  message.isEditing = true
  message.editContent = message.content
}

function cancelEditMessage(message: Message) {
  message.isEditing = false
  message.editContent = undefined
}

async function submitEditMessage(message: Message, messageIndex: number) {
  if (!message.editContent?.trim()) return

  message.content = message.editContent.trim()
  message.isEditing = false
  message.editContent = undefined

  messages.value = messages.value.slice(0, messageIndex + 1)
  isSaved.value = false
  savedMemoryId.value = null

  await sendMessageStreaming(message.content)
}

function getLastUserMessageIndex(): number {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') return i
  }
  return -1
}

async function selectMemory(source: ChatSource) {
  let memory = store.memories.find(m => m.id === source.id)

  if (memory) {
    store.selectMemory(memory)
  } else {
    store.filters.search = source.id
    await store.loadMemories()
    memory = store.memories.find(m => m.id === source.id)
    if (memory) {
      store.selectMemory(memory)
    }
  }

  emit('navigate-to-memory', source.id)
}

// Tooltip handlers
function handleSourceMouseEnter(event: MouseEvent, source: ChatSource) {
  if (hoverTimeout) clearTimeout(hoverTimeout)
  hoverTimeout = setTimeout(() => {
    const rect = (event.target as HTMLElement).getBoundingClientRect()
    tooltipPosition.value = {
      x: Math.min(rect.left, window.innerWidth - 340),
      y: rect.bottom + 8,
    }
    hoveredSource.value = source
  }, 200) // 200ms debounce
}

function handleSourceMouseLeave() {
  if (hoverTimeout) clearTimeout(hoverTimeout)
  hoveredSource.value = null
}

function getTypeColorClass(type: string): string {
  return TYPE_COLORS[type] || TYPE_COLORS.other
}

// Save conversation
async function handleSaveConversation() {
  if (isSaving.value || messages.value.length < 2) return

  isSaving.value = true
  try {
    const referencedIds = messages.value
      .filter(m => m.sources)
      .flatMap(m => m.sources!.map(s => s.id))

    const result = await saveConversation(store.currentDbPath!, {
      messages: messages.value.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
      })),
      referenced_memory_ids: [...new Set(referencedIds)],
    })

    isSaved.value = true
    savedMemoryId.value = result.memory_id
  } catch (e) {
    logger.error('Failed to save conversation:', e)
  } finally {
    isSaving.value = false
  }
}

// Export functions
function exportAsMarkdown(): string {
  let md = `# Chat Conversation\n`
  md += `**Project:** ${store.currentProject?.name || 'Unknown'}\n`
  md += `**Date:** ${new Date().toLocaleDateString()}\n\n---\n\n`

  for (const msg of messages.value) {
    const role = msg.role === 'user' ? '**You**' : '**Assistant**'
    const time = formatTime(msg.timestamp)
    md += `### ${role} (${time})\n\n${msg.content}\n\n`

    if (msg.sources?.length) {
      md += `**Sources:** ${msg.sources.map(s => s.id.slice(0, 8)).join(', ')}\n\n`
    }
    md += `---\n\n`
  }

  return md
}

function exportAsJson(): string {
  return JSON.stringify(
    {
      project: store.currentDbPath,
      exportedAt: new Date().toISOString(),
      messages: messages.value.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
        sources: m.sources,
      })),
    },
    null,
    2
  )
}

function downloadMarkdown() {
  const content = exportAsMarkdown()
  downloadFile(content, `chat_${Date.now()}.md`, 'text/markdown')
  showExportMenu.value = false
}

function downloadJson() {
  const content = exportAsJson()
  downloadFile(content, `chat_${Date.now()}.json`, 'application/json')
  showExportMenu.value = false
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function copyConversation() {
  const text = messages.value
    .map(m => `${m.role === 'user' ? 'You' : 'Assistant'}: ${m.content}`)
    .join('\n\n')
  await navigator.clipboard.writeText(text)
  showExportMenu.value = false
}

// Search functions
function searchChat() {
  if (!searchQuery.value) {
    searchResults.value = []
    return
  }

  const query = searchQuery.value.toLowerCase()
  searchResults.value = messages.value
    .map((m, i) => (m.content.toLowerCase().includes(query) ? i : -1))
    .filter(i => i !== -1)

  currentSearchIndex.value = 0
  if (searchResults.value.length > 0) {
    scrollToMessage(searchResults.value[0])
  }
}

function scrollToMessage(index: number) {
  const messageEl = document.getElementById(`message-${index}`)
  messageEl?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function nextSearchResult() {
  if (searchResults.value.length === 0) return
  currentSearchIndex.value = (currentSearchIndex.value + 1) % searchResults.value.length
  scrollToMessage(searchResults.value[currentSearchIndex.value])
}

function prevSearchResult() {
  if (searchResults.value.length === 0) return
  currentSearchIndex.value =
    (currentSearchIndex.value - 1 + searchResults.value.length) % searchResults.value.length
  scrollToMessage(searchResults.value[currentSearchIndex.value])
}

function highlightText(text: string): string {
  if (!searchQuery.value) return text
  const escapedQuery = searchQuery.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escapedQuery})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-700">$1</mark>')
}

function isMessageHighlighted(index: number): boolean {
  return searchResults.value.includes(index)
}

// Suggested prompts
function useSuggestedPrompt(prompt: string) {
  inputValue.value = prompt
  sendMessage()
}

// Follow-up actions
function sendFollowUp(text: string) {
  inputValue.value = text
  sendMessage()
}

// Utility functions
function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  return date.toLocaleDateString()
}

const emit = defineEmits<{
  (e: 'navigate-to-memory', memoryId: string): void
}>()
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <!-- Mode Toggle -->
        <div class="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-0.5">
          <button
            @click="mode = 'chat'"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="mode === 'chat'
              ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'"
          >
            <MessageCircle class="w-4 h-4" />
            Chat
          </button>
          <button
            @click="mode = 'image'"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="mode === 'image'
              ? 'bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'"
          >
            <Image class="w-4 h-4" />
            Generate
          </button>
        </div>
        <span class="font-semibold">{{ mode === 'chat' ? 'Ask About Memories' : 'Image Generation' }}</span>
      </div>

      <!-- Header Actions -->
      <div class="flex items-center gap-2">
        <!-- Search Button -->
        <button
          v-if="messages.length > 0"
          @click="showSearch = !showSearch"
          class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          title="Search (Ctrl+F)"
        >
          <Search class="w-4 h-4" />
        </button>

        <!-- Export Menu -->
        <div v-if="messages.length > 0" class="relative">
          <button
            @click="showExportMenu = !showExportMenu"
            class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            title="Export conversation"
          >
            <Download class="w-4 h-4" />
          </button>

          <div
            v-if="showExportMenu"
            class="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
          >
            <button
              @click="downloadMarkdown"
              class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <FileText class="w-4 h-4" /> Export as Markdown
            </button>
            <button
              @click="downloadJson"
              class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <FileJson class="w-4 h-4" /> Export as JSON
            </button>
            <button
              @click="copyConversation"
              class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <Clipboard class="w-4 h-4" /> Copy to Clipboard
            </button>
          </div>
        </div>

        <!-- Keyboard Shortcuts Button -->
        <button
          @click="showShortcutsHelp = true"
          class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          title="Keyboard shortcuts (Ctrl+/)"
        >
          <Keyboard class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div
      v-if="showSearch"
      class="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2 bg-gray-50 dark:bg-gray-900"
    >
      <Search class="w-4 h-4 text-gray-400" />
      <input
        id="chat-search-input"
        v-model="searchQuery"
        @input="searchChat"
        @keydown.enter="nextSearchResult"
        @keydown.escape="showSearch = false"
        placeholder="Search in conversation..."
        class="flex-1 bg-transparent border-none outline-none text-sm"
      />
      <span v-if="searchResults.length > 0" class="text-xs text-gray-500">
        {{ currentSearchIndex + 1 }} / {{ searchResults.length }}
      </span>
      <button @click="prevSearchResult" class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
        <ChevronUp class="w-4 h-4" />
      </button>
      <button @click="nextSearchResult" class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
        <ChevronDown class="w-4 h-4" />
      </button>
      <button @click="showSearch = false; searchQuery = ''" class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- Image Generation Mode -->
    <ImageGenerationPanel
      v-if="mode === 'image'"
      :chat-messages="messages.map(m => ({ role: m.role, content: m.content }))"
    />

    <!-- Chat Mode -->
    <template v-else>
    <!-- Chat Not Available -->
    <div v-if="!isChatAvailable" class="flex-1 flex items-center justify-center p-6">
      <div class="text-center">
        <AlertCircle class="w-12 h-12 mx-auto text-amber-500 mb-3" />
        <h3 class="text-lg font-medium mb-2">Chat Not Available</h3>
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-4">
          {{ chatUnavailableMessage }}
        </p>
        <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 text-left text-sm font-mono">
          <p class="text-gray-600 dark:text-gray-300">Set environment variable:</p>
          <p class="text-blue-600 dark:text-blue-400 mt-1">GEMINI_API_KEY=your_api_key</p>
        </div>
      </div>
    </div>

    <!-- Chat Available -->
    <template v-else>
      <!-- Messages -->
      <div
        ref="messagesContainer"
        class="flex-1 overflow-y-auto p-4 space-y-4"
      >
        <!-- Empty State with Suggested Prompts -->
        <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
          <div class="text-center text-gray-500 dark:text-gray-400 max-w-md">
            <Bot class="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p class="text-lg font-medium mb-3">Ask anything about your memories</p>
            <p class="text-sm mb-4">Try asking:</p>
            <div class="flex flex-wrap justify-center gap-2">
              <button
                v-for="prompt in suggestedPrompts"
                :key="prompt"
                @click="useSuggestedPrompt(prompt)"
                class="px-3 py-1.5 text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors text-left"
              >
                {{ prompt }}
              </button>
            </div>
          </div>
        </div>

        <!-- Message List -->
        <div
          v-for="(message, messageIndex) in messages"
          :id="`message-${messageIndex}`"
          :key="message.id"
          :class="[
            'flex gap-3 group',
            message.role === 'user' ? 'justify-end' : 'justify-start',
            isMessageHighlighted(messageIndex) ? 'bg-yellow-50 dark:bg-yellow-900/20 -mx-2 px-2 py-1 rounded' : ''
          ]"
        >
          <!-- Avatar -->
          <div
            v-if="message.role === 'assistant'"
            class="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center"
          >
            <Bot class="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>

          <!-- Content wrapper -->
          <div class="max-w-[80%] flex flex-col">
            <!-- Timestamp -->
            <span
              :class="[
                'text-xs text-gray-400 mb-1',
                message.role === 'user' ? 'text-right' : 'text-left'
              ]"
            >
              {{ formatRelativeTime(message.timestamp) }}
            </span>

            <!-- Message bubble -->
            <div
              :class="[
                'rounded-lg p-3',
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.error
                    ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                    : 'bg-gray-100 dark:bg-gray-700'
              ]"
            >
              <!-- User message: Edit mode or display mode -->
              <template v-if="message.role === 'user'">
                <div v-if="message.isEditing" class="space-y-2">
                  <textarea
                    v-model="message.editContent"
                    class="w-full p-2 text-sm text-gray-900 bg-white border border-gray-300 rounded resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="3"
                    @keydown.enter.ctrl="submitEditMessage(message, messageIndex)"
                  />
                  <div class="flex gap-2 justify-end">
                    <button
                      @click="cancelEditMessage(message)"
                      class="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      @click="submitEditMessage(message, messageIndex)"
                      class="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    >
                      Send
                    </button>
                  </div>
                </div>
                <p v-else class="text-sm whitespace-pre-wrap" v-html="searchQuery ? highlightText(message.content) : message.content"></p>
              </template>

              <!-- Assistant message: Markdown content with streaming indicator -->
              <div v-else>
                <div
                  class="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2"
                  @click="handleContentClick($event, message.sources)"
                  v-html="searchQuery ? highlightText(renderMarkdown(message.content, message.sources)) : renderMarkdown(message.content, message.sources)"
                ></div>

                <!-- Streaming Indicator -->
                <div v-if="message.isStreaming" class="flex items-center gap-1 mt-2">
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                </div>
              </div>

              <!-- Sources (Collapsible) with Hover Preview -->
              <div v-if="message.sources && message.sources.length > 0" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                <button
                  @click="toggleSources(message)"
                  class="flex items-center gap-1 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                >
                  <ChevronRight v-if="!message.sourcesExpanded" class="w-4 h-4" />
                  <ChevronDown v-else class="w-4 h-4" />
                  Sources ({{ message.sources.length }})
                </button>
                <div v-show="message.sourcesExpanded" class="mt-2 space-y-1">
                  <button
                    v-for="source in message.sources"
                    :key="source.id"
                    @click="selectMemory(source)"
                    @mouseenter="handleSourceMouseEnter($event, source)"
                    @mouseleave="handleSourceMouseLeave"
                    class="flex items-start gap-2 w-full text-left p-2 rounded bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                  >
                    <span :class="[getTypeColorClass(source.type), 'px-1.5 py-0.5 rounded text-xs font-medium']">
                      {{ source.type }}
                    </span>
                    <span class="flex-1 text-gray-600 dark:text-gray-300 truncate">
                      {{ source.content_preview }}
                    </span>
                    <ExternalLink class="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Action buttons (appear on hover) -->
            <div
              v-if="!message.isEditing && !isLoading && !message.isStreaming"
              :class="[
                'flex gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              ]"
            >
              <!-- Copy button (for assistant messages) -->
              <button
                v-if="message.role === 'assistant' && !message.error"
                @click="copyMessage(message)"
                class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                :title="message.copiedRecently ? 'Copied!' : 'Copy'"
              >
                <Check v-if="message.copiedRecently" class="w-3.5 h-3.5 text-green-500" />
                <Copy v-else class="w-3.5 h-3.5" />
              </button>

              <!-- Regenerate button (for the last assistant message) -->
              <button
                v-if="message.role === 'assistant' && messageIndex === messages.length - 1 && getLastUserMessageIndex() >= 0"
                @click="regenerateResponse(getLastUserMessageIndex())"
                class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                title="Regenerate response"
              >
                <RefreshCw class="w-3.5 h-3.5" />
              </button>

              <!-- Edit button (for user messages) -->
              <button
                v-if="message.role === 'user'"
                @click="startEditMessage(message)"
                class="p-1 rounded hover:bg-blue-500 text-blue-200 hover:text-white transition-colors"
                title="Edit message"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
            </div>

            <!-- Follow-up Actions (after last assistant message) -->
            <div
              v-if="message.role === 'assistant' && messageIndex === messages.length - 1 && !message.error && !isLoading && !message.isStreaming"
              class="flex flex-wrap gap-2 mt-2"
            >
              <button
                @click="sendFollowUp('Can you explain more?')"
                class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Explain more
              </button>
              <button
                @click="sendFollowUp('Can you summarize this?')"
                class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Summarize
              </button>
              <button
                @click="sendFollowUp('Try a different approach')"
                class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Different approach
              </button>
            </div>
          </div>

          <!-- User Avatar -->
          <div
            v-if="message.role === 'user'"
            class="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center"
          >
            <User class="w-5 h-5 text-white" />
          </div>
        </div>

        <!-- Loading (only when not streaming) -->
        <div v-if="isLoading && !isStreaming" class="flex gap-3">
          <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
            <Bot class="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 flex items-center gap-3">
            <Loader2 class="w-5 h-5 animate-spin text-blue-500" />
            <div class="text-sm">
              <span class="text-gray-600 dark:text-gray-300">Thinking</span>
              <span class="text-gray-400 dark:text-gray-500 ml-1">({{ elapsedTime }}s)</span>
            </div>
            <button
              @click="handleCancel"
              class="ml-2 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 hover:text-red-500 transition-colors"
              title="Cancel request"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <!-- Save Conversation Button -->
        <div v-if="messages.length > 1" class="flex justify-end mb-2">
          <button
            @click="handleSaveConversation"
            class="flex items-center gap-1 px-3 py-1.5 text-sm rounded transition-colors"
            :class="isSaved
              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
              : 'bg-green-600 text-white hover:bg-green-700'"
            :disabled="isSaving"
          >
            <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
            <Check v-else-if="isSaved" class="w-4 h-4" />
            <Bookmark v-else class="w-4 h-4" />
            {{ isSaved ? 'Saved' : isSaving ? 'Saving...' : 'Save Chat' }}
          </button>
        </div>

        <div class="flex gap-2">
          <div class="flex-1 relative">
            <textarea
              ref="inputRef"
              v-model="inputValue"
              @keydown="handleKeyDown"
              :disabled="isLoading"
              placeholder="Ask about your memories..."
              class="w-full px-3 py-2 pr-16 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              rows="2"
              :maxlength="maxChars"
            />
            <span
              :class="[
                'absolute bottom-2 right-2 text-xs',
                charCount > maxChars * 0.9 ? 'text-amber-500' : 'text-gray-400'
              ]"
            >
              {{ charCount }} / {{ maxChars }}
            </span>
          </div>
          <button
            @click="sendMessage"
            :disabled="!inputValue.trim() || isLoading"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          >
            <Send class="w-5 h-5" />
          </button>
        </div>

        <!-- Cancel button during streaming -->
        <div v-if="isStreaming" class="flex justify-center mt-2">
          <button
            @click="handleCancel"
            class="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
          >
            <X class="w-4 h-4" /> Stop Generating
          </button>
        </div>
      </div>
    </template>
    </template>

    <!-- Source Tooltip -->
    <SourceTooltip
      v-if="hoveredSource"
      :source="hoveredSource"
      :position="tooltipPosition"
    />

    <!-- Keyboard Shortcuts Modal -->
    <div
      v-if="showShortcutsHelp"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showShortcutsHelp = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <h3 class="text-lg font-semibold mb-4">Keyboard Shortcuts</h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between py-1">
            <span>Send message</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Enter</kbd>
          </div>
          <div class="flex justify-between py-1">
            <span>New line</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Shift + Enter</kbd>
          </div>
          <div class="flex justify-between py-1">
            <span>Cancel request</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Escape</kbd>
          </div>
          <div class="flex justify-between py-1">
            <span>Edit last message</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">↑ (empty input)</kbd>
          </div>
          <div class="flex justify-between py-1">
            <span>Submit edit</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Ctrl + Enter</kbd>
          </div>
          <div class="flex justify-between py-1">
            <span>Search in chat</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Ctrl + F</kbd>
          </div>
          <div class="flex justify-between py-1">
            <span>This help</span>
            <kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">Ctrl + /</kbd>
          </div>
        </div>
        <button
          @click="showShortcutsHelp = false"
          class="mt-4 w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-6px);
  }
}
.animate-bounce {
  animation: bounce 1.4s ease-in-out infinite;
}
</style>
