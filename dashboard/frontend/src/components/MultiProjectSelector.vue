<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { Globe, Folder, Star, Settings } from 'lucide-vue-next'
import type { Project } from '@/types'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'openManagement'): void
}>()

const store = useDashboardStore()

const selectedCount = computed(() => store.selectedProjects.length)

function isSelected(project: Project): boolean {
  return store.selectedProjects.some(p => p.db_path === project.db_path)
}

function handleToggle(project: Project) {
  store.toggleProjectSelection(project)
}

function handleSelectAll() {
  store.selectAllProjects()
}

function handleClearAll() {
  store.clearProjectSelection()
}

// Close on click outside
function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.multi-project-selector')) {
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
  <div class="multi-project-selector absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 max-h-96 overflow-hidden flex flex-col animate-fade-in z-50">
    <!-- Header with Select All / Clear -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
      <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
        Projects
      </span>
      <div class="flex gap-2">
        <button
          @click.stop="handleSelectAll"
          class="text-xs text-blue-500 hover:text-blue-700 dark:hover:text-blue-400 px-2 py-1 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30"
        >
          Select All
        </button>
        <button
          @click.stop="handleClearAll"
          class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          Clear
        </button>
        <button
          @click.stop="emit('openManagement')"
          class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <Settings class="w-3 h-3" />
          Manage
        </button>
      </div>
    </div>

    <!-- Project List with Checkboxes -->
    <div class="overflow-y-auto flex-1">
      <div v-if="store.projects.length === 0" class="px-3 py-4 text-center text-gray-500">
        No projects found
      </div>

      <label
        v-for="project in store.projects"
        :key="project.db_path"
        :class="[
          'flex items-start gap-3 px-3 py-2 cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50',
          isSelected(project) ? 'bg-blue-50 dark:bg-blue-900/20' : ''
        ]"
      >
        <!-- Checkbox -->
        <input
          type="checkbox"
          :checked="isSelected(project)"
          @change="handleToggle(project)"
          class="mt-1 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
        />

        <!-- Icon -->
        <div class="flex-shrink-0 mt-0.5">
          <Globe v-if="project.is_global" class="w-5 h-5 text-purple-500" />
          <Folder v-else class="w-5 h-5 text-gray-400" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0 relative">
          <!-- Favorite indicator -->
          <Star
            v-if="project.is_favorite"
            class="w-3 h-3 text-yellow-500 fill-yellow-500 absolute -top-1 right-0"
          />

          <div class="font-medium truncate pr-4">{{ project.display_name || project.name }}</div>
          <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
            {{ project.memory_count }} memories
          </div>
        </div>
      </label>
    </div>

    <!-- Selection Summary -->
    <div
      v-if="selectedCount > 0"
      class="px-3 py-2 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium border-t border-blue-100 dark:border-blue-800 flex-shrink-0"
    >
      {{ selectedCount }} project{{ selectedCount > 1 ? 's' : '' }} selected
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.15s ease-out;
}
</style>
