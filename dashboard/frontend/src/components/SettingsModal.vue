<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  X,
  Key,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Copy,
  Check,
  Settings,
  Image,
  MessageCircle,
} from 'lucide-vue-next'
import { getImageStatus, getChatStatus } from '@/services/api'
import { useDashboardStore } from '@/stores/dashboardStore'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()

// Status
const imageStatus = ref<{ available: boolean; message: string } | null>(null)
const chatStatus = ref<{ available: boolean; message: string } | null>(null)
const isLoading = ref(true)
const copiedCommand = ref<string | null>(null)

// Command strings for copying
const psCommand = '$env:GEMINI_API_KEY="your-api-key-here"'
const unixCommand = 'export GEMINI_API_KEY="your-api-key-here"'

onMounted(async () => {
  await checkStatus()
})

async function checkStatus() {
  isLoading.value = true
  try {
    const [imgStatus, chtStatus] = await Promise.all([
      getImageStatus(),
      store.currentDbPath ? getChatStatus(store.currentDbPath) : Promise.resolve({ available: false, message: 'No project selected' }),
    ])
    imageStatus.value = imgStatus
    chatStatus.value = chtStatus
  } catch (e) {
    console.error('Failed to check status:', e)
  } finally {
    isLoading.value = false
  }
}

async function copyToClipboard(text: string, id: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedCommand.value = id
    setTimeout(() => {
      copiedCommand.value = null
    }, 2000)
  } catch (e) {
    console.error('Failed to copy:', e)
  }
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    @click.self="emit('close')"
  >
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Settings class="w-5 h-5 text-gray-500 dark:text-gray-400" />
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">Settings</h2>
        </div>
        <button
          @click="emit('close')"
          class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <X class="w-5 h-5 text-gray-500 dark:text-gray-400" />
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- API Status Overview -->
        <section>
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3 flex items-center gap-2">
            <Key class="w-4 h-4" />
            API Status
          </h3>

          <div class="space-y-3">
            <!-- Chat API Status -->
            <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
              <div class="flex items-center gap-3">
                <MessageCircle class="w-5 h-5 text-blue-500" />
                <div>
                  <p class="text-sm font-medium text-gray-800 dark:text-gray-100">Ask AI (Chat)</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Gemini API for chat</p>
                </div>
              </div>
              <div v-if="isLoading" class="text-sm text-gray-400">Checking...</div>
              <div v-else-if="chatStatus?.available" class="flex items-center gap-1 text-green-600 dark:text-green-400">
                <CheckCircle class="w-4 h-4" />
                <span class="text-sm font-medium">Connected</span>
              </div>
              <div v-else class="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                <AlertTriangle class="w-4 h-4" />
                <span class="text-sm font-medium">Not configured</span>
              </div>
            </div>

            <!-- Image Generation Status -->
            <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
              <div class="flex items-center gap-3">
                <Image class="w-5 h-5 text-purple-500" />
                <div>
                  <p class="text-sm font-medium text-gray-800 dark:text-gray-100">Image Generation</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Nano Banana Pro (Gemini)</p>
                </div>
              </div>
              <div v-if="isLoading" class="text-sm text-gray-400">Checking...</div>
              <div v-else-if="imageStatus?.available" class="flex items-center gap-1 text-green-600 dark:text-green-400">
                <CheckCircle class="w-4 h-4" />
                <span class="text-sm font-medium">Ready</span>
              </div>
              <div v-else class="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                <AlertTriangle class="w-4 h-4" />
                <span class="text-sm font-medium">Not configured</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Configuration Instructions -->
        <section v-if="!imageStatus?.available || !chatStatus?.available">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
            Setup Instructions
          </h3>

          <div class="space-y-4">
            <!-- Step 1: Get API Key -->
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center text-sm font-semibold">1</div>
                <div class="flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-gray-100 mb-1">Get a Gemini API Key</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    Create a free API key from Google AI Studio.
                  </p>
                  <a
                    href="https://aistudio.google.com/apikey"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Open Google AI Studio
                    <ExternalLink class="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>

            <!-- Step 2: Install Package -->
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center text-sm font-semibold">2</div>
                <div class="flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-gray-100 mb-1">Install the google-genai Package</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    Run this command in your terminal:
                  </p>
                  <div class="flex items-center gap-2">
                    <code class="flex-1 px-3 py-2 bg-gray-900 dark:bg-gray-950 text-green-400 rounded text-sm font-mono">
                      pip install google-genai
                    </code>
                    <button
                      @click="copyToClipboard('pip install google-genai', 'pip')"
                      class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                      title="Copy command"
                    >
                      <Check v-if="copiedCommand === 'pip'" class="w-4 h-4 text-green-500" />
                      <Copy v-else class="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 3: Set Environment Variable -->
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center text-sm font-semibold">3</div>
                <div class="flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-gray-100 mb-1">Set the Environment Variable</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    Add the GEMINI_API_KEY to your environment or .env file:
                  </p>

                  <!-- Tabs for different OS -->
                  <div class="space-y-2">
                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Windows (PowerShell):</p>
                      <div class="flex items-center gap-2">
                        <code class="flex-1 px-3 py-2 bg-gray-900 dark:bg-gray-950 text-green-400 rounded text-sm font-mono overflow-x-auto">
                          $env:GEMINI_API_KEY="your-api-key-here"
                        </code>
                        <button
                          @click="copyToClipboard(psCommand, 'ps')"
                          class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                          title="Copy command"
                        >
                          <Check v-if="copiedCommand === 'ps'" class="w-4 h-4 text-green-500" />
                          <Copy v-else class="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">macOS/Linux:</p>
                      <div class="flex items-center gap-2">
                        <code class="flex-1 px-3 py-2 bg-gray-900 dark:bg-gray-950 text-green-400 rounded text-sm font-mono overflow-x-auto">
                          export GEMINI_API_KEY="your-api-key-here"
                        </code>
                        <button
                          @click="copyToClipboard(unixCommand, 'unix')"
                          class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                          title="Copy command"
                        >
                          <Check v-if="copiedCommand === 'unix'" class="w-4 h-4 text-green-500" />
                          <Copy v-else class="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">.env file (recommended):</p>
                      <div class="flex items-center gap-2">
                        <code class="flex-1 px-3 py-2 bg-gray-900 dark:bg-gray-950 text-green-400 rounded text-sm font-mono overflow-x-auto">
                          GEMINI_API_KEY=your-api-key-here
                        </code>
                        <button
                          @click="copyToClipboard('GEMINI_API_KEY=your-api-key-here', 'env')"
                          class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                          title="Copy command"
                        >
                          <Check v-if="copiedCommand === 'env'" class="w-4 h-4 text-green-500" />
                          <Copy v-else class="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 4: Restart -->
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center text-sm font-semibold">4</div>
                <div class="flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-gray-100 mb-1">Restart the Dashboard</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-300">
                    After setting the environment variable, restart the Omni-Cortex dashboard server for changes to take effect.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- All configured message -->
        <section v-if="imageStatus?.available && chatStatus?.available">
          <div class="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <div class="flex items-center gap-3">
              <CheckCircle class="w-5 h-5 text-green-600 dark:text-green-400" />
              <div>
                <p class="text-sm font-medium text-green-800 dark:text-green-200">All AI features are configured!</p>
                <p class="text-sm text-green-600 dark:text-green-300 mt-0.5">
                  Both Chat and Image Generation are ready to use.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <button
          @click="checkStatus"
          :disabled="isLoading"
          class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
        >
          Refresh Status
        </button>
        <button
          @click="emit('close')"
          class="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  </div>
</template>
