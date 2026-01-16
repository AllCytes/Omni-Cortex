<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { composeResponse } from '@/services/api'
import type { ContextType, ResponseTemplate, ComposedResponse } from '@/types'
import {
  MessageSquare, Mail, Users, AtSign, FileText,
  Wand2, Copy, Check, History, Sparkles,
  SlidersHorizontal, RefreshCw, Eraser, HelpCircle
} from 'lucide-vue-next'

const store = useDashboardStore()

// Input state
const incomingMessage = ref('')
const contextType = ref<ContextType>('general')
const selectedTemplate = ref<ResponseTemplate | null>(null)
const toneLevel = ref(50) // 0-100 slider
const includeMemories = ref(true)
const customInstructions = ref('')
const includeExplanation = ref(false)

// Output state
const generatedResponse = ref('')
const explanation = ref('')
const isGenerating = ref(false)
const responseHistory = ref<ComposedResponse[]>([])
const copiedRecently = ref(false)
const errorMessage = ref('')

// Context type options with icons
const contextOptions = [
  { value: 'skool_post' as ContextType, label: 'Skool Post', icon: Users },
  { value: 'dm' as ContextType, label: 'Direct Message', icon: MessageSquare },
  { value: 'email' as ContextType, label: 'Email', icon: Mail },
  { value: 'comment' as ContextType, label: 'Comment Thread', icon: AtSign },
  { value: 'general' as ContextType, label: 'General', icon: FileText },
]

// Quick templates
const templates = [
  { value: 'answer' as ResponseTemplate, label: 'Answer Question', desc: 'Direct answer with explanation' },
  { value: 'guide' as ResponseTemplate, label: 'Provide Guidance', desc: 'Step-by-step recommendations' },
  { value: 'redirect' as ResponseTemplate, label: 'Redirect to Resource', desc: 'Point to helpful resource' },
  { value: 'acknowledge' as ResponseTemplate, label: 'Acknowledge & Follow-up', desc: 'Validate and ask more' },
]

// Tone labels
const toneLabel = computed(() => {
  if (toneLevel.value < 25) return 'Very Casual'
  if (toneLevel.value < 50) return 'Casual'
  if (toneLevel.value < 75) return 'Professional'
  return 'Very Professional'
})

async function generate() {
  if (!incomingMessage.value.trim() || !store.currentDbPath) return

  isGenerating.value = true
  errorMessage.value = ''
  try {
    const result = await composeResponse(store.currentDbPath, {
      incoming_message: incomingMessage.value,
      context_type: contextType.value,
      template: selectedTemplate.value || undefined,
      tone_level: toneLevel.value,
      include_memories: includeMemories.value,
      custom_instructions: customInstructions.value || undefined,
      include_explanation: includeExplanation.value,
    })

    generatedResponse.value = result.response
    explanation.value = result.explanation || ''
    responseHistory.value.unshift(result)

    // Keep only last 10 items in history
    if (responseHistory.value.length > 10) {
      responseHistory.value = responseHistory.value.slice(0, 10)
    }
  } catch (e) {
    console.error('Failed to generate response:', e)
    errorMessage.value = e instanceof Error ? e.message : 'Failed to generate response'
  } finally {
    isGenerating.value = false
  }
}

async function copyResponse() {
  await navigator.clipboard.writeText(generatedResponse.value)
  copiedRecently.value = true
  setTimeout(() => copiedRecently.value = false, 2000)
}

function regenerate() {
  generate()
}

function useHistoryItem(item: ComposedResponse) {
  generatedResponse.value = item.response
  incomingMessage.value = item.incoming_message
  contextType.value = item.context_type
  toneLevel.value = item.tone_level
  if (item.template_used) {
    selectedTemplate.value = item.template_used
  }
  customInstructions.value = item.custom_instructions || ''
  explanation.value = item.explanation || ''
}

function clearAll() {
  incomingMessage.value = ''
  customInstructions.value = ''
  contextType.value = 'general'
  selectedTemplate.value = null
  toneLevel.value = 50
  includeMemories.value = true
  includeExplanation.value = false
  generatedResponse.value = ''
  explanation.value = ''
  errorMessage.value = ''
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <Wand2 class="w-5 h-5 text-indigo-500" />
        Response Composer
      </h2>
      <p class="text-sm text-gray-500 mt-1">
        Paste a message and generate a response in your voice
      </p>
    </div>

    <div class="flex-1 overflow-auto p-4">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left: Input Section -->
        <div class="space-y-4">
          <!-- Context Type Selector -->
          <div>
            <label class="block text-sm font-medium mb-2">Message Source</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="opt in contextOptions"
                :key="opt.value"
                @click="contextType = opt.value"
                :class="[
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                  contextType === opt.value
                    ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 ring-2 ring-indigo-500'
                    : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                ]"
              >
                <component :is="opt.icon" class="w-4 h-4" />
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Incoming Message Input -->
          <div>
            <label class="block text-sm font-medium mb-2">Incoming Message</label>
            <textarea
              v-model="incomingMessage"
              placeholder="Paste the message you want to respond to..."
              rows="8"
              class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 resize-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <!-- Custom Instructions -->
          <div>
            <label class="block text-sm font-medium mb-2">
              Your Instructions (Optional)
            </label>
            <textarea
              v-model="customInstructions"
              placeholder="Add specific requirements, questions to ask, or things to include in the response..."
              rows="3"
              class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 resize-none focus:ring-2 focus:ring-indigo-500"
            />
            <p class="text-xs text-gray-500 mt-1">
              E.g., "Ask them about their timeline" or "Include a resource link"
            </p>
          </div>

          <!-- Quick Templates -->
          <div>
            <label class="block text-sm font-medium mb-2">Response Template (Optional)</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="tpl in templates"
                :key="tpl.value"
                @click="selectedTemplate = selectedTemplate === tpl.value ? null : tpl.value"
                :class="[
                  'p-3 rounded-lg text-left transition-colors',
                  selectedTemplate === tpl.value
                    ? 'bg-indigo-100 dark:bg-indigo-900/30 ring-2 ring-indigo-500'
                    : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                ]"
              >
                <div class="font-medium text-sm">{{ tpl.label }}</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ tpl.desc }}</div>
              </button>
            </div>
          </div>

          <!-- Options -->
          <div class="flex items-center gap-4 flex-wrap">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="includeMemories" class="rounded" />
              <span class="text-sm">Include knowledge from memories</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="includeExplanation" class="rounded" />
              <span class="text-sm">Explain message to me first</span>
            </label>
          </div>

          <!-- Action Buttons -->
          <div class="flex gap-2">
            <button
              @click="generate"
              :disabled="!incomingMessage.trim() || isGenerating"
              class="flex-1 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
            >
              <Sparkles v-if="!isGenerating" class="w-5 h-5" />
              <RefreshCw v-else class="w-5 h-5 animate-spin" />
              {{ isGenerating ? 'Generating...' : 'Generate Response' }}
            </button>
            <button
              @click="clearAll"
              class="px-4 py-3 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg flex items-center gap-2 transition-colors"
              title="Clear all fields"
            >
              <Eraser class="w-4 h-4" />
              <span class="text-sm font-medium">Clear</span>
            </button>
          </div>

          <!-- Error Message -->
          <div v-if="errorMessage" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300">
            {{ errorMessage }}
          </div>
        </div>

        <!-- Right: Output Section -->
        <div class="space-y-4">
          <!-- Tone Slider -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium flex items-center gap-2">
                <SlidersHorizontal class="w-4 h-4" />
                Tone Adjustment
              </label>
              <span class="text-sm text-indigo-600 dark:text-indigo-400 font-medium">
                {{ toneLabel }}
              </span>
            </div>
            <input
              type="range"
              v-model.number="toneLevel"
              min="0"
              max="100"
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div class="flex justify-between text-xs text-gray-400 mt-1">
              <span>Casual</span>
              <span>Professional</span>
            </div>
          </div>

          <!-- Explanation Section -->
          <div v-if="explanation" class="mb-4">
            <label class="block text-sm font-medium mb-2 flex items-center gap-2">
              <HelpCircle class="w-4 h-4 text-blue-500" />
              What This Message Means
            </label>
            <div class="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm">
              {{ explanation }}
            </div>
          </div>

          <!-- Generated Response -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium">Generated Response</label>
              <div class="flex items-center gap-2">
                <button
                  v-if="generatedResponse"
                  @click="regenerate"
                  class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                  title="Regenerate"
                >
                  <RefreshCw class="w-4 h-4" />
                </button>
                <button
                  v-if="generatedResponse"
                  @click="copyResponse"
                  class="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                >
                  <Check v-if="copiedRecently" class="w-4 h-4" />
                  <Copy v-else class="w-4 h-4" />
                  {{ copiedRecently ? 'Copied!' : 'Copy' }}
                </button>
              </div>
            </div>
            <textarea
              v-model="generatedResponse"
              placeholder="Your response will appear here..."
              rows="12"
              class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 resize-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      <!-- Response History -->
      <div v-if="responseHistory.length > 0" class="mt-8">
        <h3 class="text-sm font-medium flex items-center gap-2 mb-3">
          <History class="w-4 h-4" />
          Recent Responses
        </h3>
        <div class="space-y-2">
          <button
            v-for="item in responseHistory.slice(0, 5)"
            :key="item.id"
            @click="useHistoryItem(item)"
            class="w-full p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="text-sm font-medium truncate">{{ item.incoming_message.slice(0, 60) }}...</div>
            <div class="text-xs text-gray-500 mt-1">
              {{ item.context_type }} | {{ item.template_used || 'No template' }}
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
