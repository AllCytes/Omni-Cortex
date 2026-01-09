<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { askAboutMemories, getChatStatus, cancelChatRequest, type ChatSource } from '@/services/api'
import { Send, Loader2, MessageCircle, AlertCircle, Bot, User, ExternalLink, ChevronDown, ChevronRight, X, Copy, Check, RefreshCw, Pencil } from 'lucide-vue-next'
import { marked } from 'marked'

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
}

const store = useDashboardStore()
const messages = ref<Message[]>([])
const inputValue = ref('')
const isLoading = ref(false)
const isChatAvailable = ref(false)
const chatUnavailableMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const elapsedTime = ref(0)
let elapsedTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await checkChatStatus()
})

onUnmounted(() => {
  stopElapsedTimer()
  cancelChatRequest()
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
  stopElapsedTimer()
  isLoading.value = false

  const cancelMessage: Message = {
    id: `msg_${Date.now()}_cancelled`,
    role: 'assistant',
    content: 'Request cancelled.',
    timestamp: new Date(),
    error: false,
  }
  messages.value.push(cancelMessage)
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

  // Add user message
  const userMessage: Message = {
    id: `msg_${Date.now()}_user`,
    role: 'user',
    content: question,
    timestamp: new Date(),
  }
  messages.value.push(userMessage)
  scrollToBottom()

  // Send to API
  isLoading.value = true
  startElapsedTimer()
  try {
    const response = await askAboutMemories(store.currentDbPath, question)

    const assistantMessage: Message = {
      id: `msg_${Date.now()}_assistant`,
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      timestamp: new Date(),
      error: !!response.error,
      sourcesExpanded: false,
    }
    messages.value.push(assistantMessage)
  } catch (e) {
    // Don't show error for cancelled requests (already handled)
    if (e instanceof Error && e.message === 'Request cancelled') {
      return
    }
    const errorMessage: Message = {
      id: `msg_${Date.now()}_error`,
      role: 'assistant',
      content: e instanceof Error ? e.message : 'Failed to get response',
      timestamp: new Date(),
      error: true,
    }
    messages.value.push(errorMessage)
  } finally {
    stopElapsedTimer()
    isLoading.value = false
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

function renderMarkdown(content: string): string {
  return marked.parse(content) as string
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
    console.error('Failed to copy:', e)
  }
}

async function regenerateResponse(userMessageIndex: number) {
  // Find the user message at the given index
  const userMessage = messages.value[userMessageIndex]
  if (!userMessage || userMessage.role !== 'user') return

  // Remove all messages after this user message
  messages.value = messages.value.slice(0, userMessageIndex + 1)

  // Resend the question
  const question = userMessage.content

  isLoading.value = true
  startElapsedTimer()
  try {
    const response = await askAboutMemories(store.currentDbPath!, question)

    const assistantMessage: Message = {
      id: `msg_${Date.now()}_assistant`,
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      timestamp: new Date(),
      error: !!response.error,
      sourcesExpanded: false,
    }
    messages.value.push(assistantMessage)
  } catch (e) {
    if (e instanceof Error && e.message === 'Request cancelled') return
    const errorMessage: Message = {
      id: `msg_${Date.now()}_error`,
      role: 'assistant',
      content: e instanceof Error ? e.message : 'Failed to get response',
      timestamp: new Date(),
      error: true,
    }
    messages.value.push(errorMessage)
  } finally {
    stopElapsedTimer()
    isLoading.value = false
    scrollToBottom()
  }
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

  // Update the message content
  message.content = message.editContent.trim()
  message.isEditing = false
  message.editContent = undefined

  // Remove all messages after this one and regenerate
  messages.value = messages.value.slice(0, messageIndex + 1)

  // Resend with edited content
  isLoading.value = true
  startElapsedTimer()
  try {
    const response = await askAboutMemories(store.currentDbPath!, message.content)

    const assistantMessage: Message = {
      id: `msg_${Date.now()}_assistant`,
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      timestamp: new Date(),
      error: !!response.error,
      sourcesExpanded: false,
    }
    messages.value.push(assistantMessage)
  } catch (e) {
    if (e instanceof Error && e.message === 'Request cancelled') return
    const errorMessage: Message = {
      id: `msg_${Date.now()}_error`,
      role: 'assistant',
      content: e instanceof Error ? e.message : 'Failed to get response',
      timestamp: new Date(),
      error: true,
    }
    messages.value.push(errorMessage)
  } finally {
    stopElapsedTimer()
    isLoading.value = false
    scrollToBottom()
  }
}

function getLastUserMessageIndex(): number {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') return i
  }
  return -1
}

async function selectMemory(source: ChatSource) {
  // First, try to find in current loaded memories
  let memory = store.memories.find(m => m.id === source.id)

  if (memory) {
    store.selectMemory(memory)
  } else {
    // Memory not loaded - search for it and switch to Memories tab
    store.filters.search = source.id
    await store.loadMemories()
    memory = store.memories.find(m => m.id === source.id)
    if (memory) {
      store.selectMemory(memory)
    }
  }

  // Emit event to switch to Memories tab (parent component handles this)
  emit('navigate-to-memory', source.id)
}

const emit = defineEmits<{
  (e: 'navigate-to-memory', memoryId: string): void
}>()
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
      <MessageCircle class="w-5 h-5 text-blue-600" />
      <span class="font-semibold">Ask About Memories</span>
    </div>

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
        <!-- Empty State -->
        <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
          <div class="text-center text-gray-500 dark:text-gray-400">
            <Bot class="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p class="text-lg font-medium mb-2">Ask anything about your memories</p>
            <p class="text-sm">Examples:</p>
            <ul class="text-sm mt-2 space-y-1">
              <li>"What decisions have I made about authentication?"</li>
              <li>"Summarize my recent solutions"</li>
              <li>"What errors have I encountered with Vue?"</li>
            </ul>
          </div>
        </div>

        <!-- Message List -->
        <div
          v-for="(message, messageIndex) in messages"
          :key="message.id"
          :class="[
            'flex gap-3 group',
            message.role === 'user' ? 'justify-end' : 'justify-start'
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
                <p v-else class="text-sm whitespace-pre-wrap">{{ message.content }}</p>
              </template>

              <!-- Assistant message: Markdown content -->
              <div
                v-else
                class="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2"
                v-html="renderMarkdown(message.content)"
              ></div>

              <!-- Sources (Collapsible) -->
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
                    class="flex items-start gap-2 w-full text-left p-2 rounded bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                  >
                    <span class="px-1.5 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
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
              v-if="!message.isEditing && !isLoading"
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
          </div>

          <!-- User Avatar -->
          <div
            v-if="message.role === 'user'"
            class="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center"
          >
            <User class="w-5 h-5 text-white" />
          </div>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="flex gap-3">
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

      <!-- Input -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex gap-2">
          <textarea
            v-model="inputValue"
            @keydown="handleKeyDown"
            :disabled="isLoading"
            placeholder="Ask about your memories..."
            class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            rows="2"
          />
          <button
            @click="sendMessage"
            :disabled="!inputValue.trim() || isLoading"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          >
            <Send class="w-5 h-5" />
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
