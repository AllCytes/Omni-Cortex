<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import type { Project } from '@/types'
import {
  X, FolderPlus, FolderSearch, Star, StarOff,
  Trash2, RefreshCw
} from 'lucide-vue-next'
import * as api from '@/services/api'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()

// Tabs
type Tab = 'projects' | 'directories' | 'add'
const activeTab = ref<Tab>('projects')

// Add project form
const newProjectPath = ref('')
const newProjectName = ref('')
const isAdding = ref(false)
const addError = ref('')

// New directory form
const newDirectory = ref('')
const isAddingDir = ref(false)

// Refresh state
const isRefreshing = ref(false)

// Computed
const registeredProjects = computed(() =>
  store.projects.filter(p => p.is_registered)
)

const favoriteProjects = computed(() =>
  store.projects.filter(p => p.is_favorite)
)

// Actions
async function addProject() {
  if (!newProjectPath.value.trim()) return

  isAdding.value = true
  addError.value = ''

  try {
    await api.registerProject(
      newProjectPath.value.trim(),
      newProjectName.value.trim() || undefined
    )
    await store.loadProjects()
    newProjectPath.value = ''
    newProjectName.value = ''
    activeTab.value = 'projects'
  } catch (e) {
    addError.value = 'Failed to add project. Check path has .omni-cortex/cortex.db'
  } finally {
    isAdding.value = false
  }
}

async function removeProject(path: string) {
  try {
    await api.unregisterProject(path)
    await store.loadProjects()
  } catch (e) {
    console.error('Failed to remove project:', e)
  }
}

async function handleToggleFavorite(project: Project) {
  try {
    await api.toggleFavorite(project.path)
    await store.loadProjects()
  } catch (e) {
    console.error('Failed to toggle favorite:', e)
  }
}

async function addDirectory() {
  if (!newDirectory.value.trim()) return

  isAddingDir.value = true
  try {
    await api.addScanDirectory(newDirectory.value.trim())
    await store.loadProjectConfig()
    await store.loadProjects()
    newDirectory.value = ''
  } catch (e) {
    console.error('Failed to add directory:', e)
  } finally {
    isAddingDir.value = false
  }
}

async function removeDirectory(dir: string) {
  try {
    await api.removeScanDirectory(dir)
    await store.loadProjectConfig()
    await store.loadProjects()
  } catch (e) {
    console.error('Failed to remove directory:', e)
  }
}

async function refreshAll() {
  isRefreshing.value = true
  try {
    await api.refreshProjects()
    await store.loadProjects()
  } finally {
    isRefreshing.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h2 class="text-lg font-semibold">Project Management</h2>
        <button @click="emit('close')" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b dark:border-gray-700">
        <button
          v-for="tab in (['projects', 'directories', 'add'] as Tab[])"
          :key="tab"
          @click="activeTab = tab"
          :class="[
            'px-4 py-3 font-medium capitalize',
            activeTab === tab
              ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
              : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
        >
          {{ tab === 'add' ? 'Add Project' : tab }}
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- Projects Tab -->
        <template v-if="activeTab === 'projects'">
          <!-- Favorites Section -->
          <div v-if="favoriteProjects.length" class="mb-6">
            <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">Favorites</h3>
            <div class="space-y-2">
              <div
                v-for="project in favoriteProjects"
                :key="project.path"
                class="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg"
              >
                <Star class="w-5 h-5 text-yellow-500 fill-yellow-500 flex-shrink-0" />
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate">{{ project.display_name || project.name }}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ project.path }}</div>
                </div>
                <button @click="handleToggleFavorite(project)" class="p-2 hover:bg-yellow-100 dark:hover:bg-yellow-900/40 rounded">
                  <StarOff class="w-4 h-4 text-yellow-600" />
                </button>
              </div>
            </div>
          </div>

          <!-- All Projects -->
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">All Projects</h3>
          <div class="space-y-2">
            <div
              v-for="project in store.projects"
              :key="project.path"
              class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">
                  {{ project.display_name || project.name }}
                  <span v-if="project.is_registered" class="text-xs text-blue-500 ml-2">(registered)</span>
                  <span v-if="project.is_global" class="text-xs text-purple-500 ml-2">(global)</span>
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ project.path }}</div>
              </div>
              <button
                @click="handleToggleFavorite(project)"
                class="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
              >
                <Star :class="['w-4 h-4', project.is_favorite ? 'text-yellow-500 fill-yellow-500' : 'text-gray-400']" />
              </button>
              <button
                v-if="project.is_registered"
                @click="removeProject(project.path)"
                class="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </template>

        <!-- Directories Tab -->
        <template v-else-if="activeTab === 'directories'">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            These directories are automatically scanned for OmniCortex projects.
          </p>

          <!-- Add Directory Form -->
          <div class="flex gap-2 mb-4">
            <input
              v-model="newDirectory"
              placeholder="Enter directory path (e.g., ~/my-projects)"
              class="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              @click="addDirectory"
              :disabled="isAddingDir || !newDirectory.trim()"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              Add
            </button>
          </div>

          <!-- Directory List -->
          <div class="space-y-2">
            <div
              v-for="dir in store.projectConfig?.scan_directories"
              :key="dir"
              class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <FolderSearch class="w-5 h-5 text-gray-400 flex-shrink-0" />
              <span class="flex-1 truncate">{{ dir }}</span>
              <button
                @click="removeDirectory(dir)"
                class="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
            <div v-if="!store.projectConfig?.scan_directories?.length" class="text-center text-gray-500 py-4">
              No scan directories configured
            </div>
          </div>
        </template>

        <!-- Add Project Tab -->
        <template v-else-if="activeTab === 'add'">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Add a project from any location. The path must contain a <code class="bg-gray-200 dark:bg-gray-700 px-1 rounded">.omni-cortex/cortex.db</code> file.
          </p>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">Project Path *</label>
              <input
                v-model="newProjectPath"
                placeholder="C:/Users/Me/custom-project"
                class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Display Name (optional)</label>
              <input
                v-model="newProjectName"
                placeholder="My Custom Project"
                class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div v-if="addError" class="text-red-500 text-sm">
              {{ addError }}
            </div>

            <button
              @click="addProject"
              :disabled="isAdding || !newProjectPath.trim()"
              class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <FolderPlus class="w-5 h-5" />
              Add Project
            </button>
          </div>

          <!-- Registered Projects -->
          <div v-if="registeredProjects.length" class="mt-6">
            <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">Registered Projects</h3>
            <div class="space-y-2">
              <div
                v-for="project in registeredProjects"
                :key="project.path"
                class="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
              >
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate">{{ project.display_name || project.name }}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ project.path }}</div>
                </div>
                <button
                  @click="removeProject(project.path)"
                  class="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div class="flex justify-between items-center p-4 border-t dark:border-gray-700">
        <button
          @click="refreshAll"
          :disabled="isRefreshing"
          class="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 disabled:opacity-50"
        >
          <RefreshCw :class="['w-4 h-4', isRefreshing && 'animate-spin']" />
          Refresh All
        </button>
        <button
          @click="emit('close')"
          class="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
        >
          Done
        </button>
      </div>
    </div>
  </div>
</template>
