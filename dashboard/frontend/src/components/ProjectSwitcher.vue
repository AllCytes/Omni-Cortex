<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { Globe, Folder, Clock } from 'lucide-vue-next'
import type { Project } from '@/types'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useDashboardStore()

function selectProject(project: Project) {
  store.switchProject(project)
  emit('close')
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never'
  const date = new Date(dateStr)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// Close on click outside
function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.project-switcher')) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
})
</script>

<template>
  <div class="project-switcher absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto animate-fade-in z-50">
    <div class="p-2">
      <div class="text-xs font-semibold text-gray-500 dark:text-gray-400 px-3 py-2 uppercase">
        Projects
      </div>

      <div v-if="store.projects.length === 0" class="px-3 py-4 text-center text-gray-500">
        No projects found
      </div>

      <button
        v-for="project in store.projects"
        :key="project.db_path"
        @click="selectProject(project)"
        :class="[
          'w-full px-3 py-2 rounded-lg text-left transition-colors flex items-start gap-3',
          store.currentProject?.db_path === project.db_path
            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
            : 'hover:bg-gray-100 dark:hover:bg-gray-700'
        ]"
      >
        <!-- Icon -->
        <div class="flex-shrink-0 mt-0.5">
          <Globe v-if="project.is_global" class="w-5 h-5 text-purple-500" />
          <Folder v-else class="w-5 h-5 text-gray-400" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="font-medium truncate">{{ project.name }}</div>
          <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
            {{ project.path }}
          </div>
          <div class="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
            <span>{{ project.memory_count }} memories</span>
            <span class="flex items-center gap-1">
              <Clock class="w-3 h-3" />
              {{ formatDate(project.last_modified) }}
            </span>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>
