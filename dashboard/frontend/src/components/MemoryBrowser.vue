<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import MemoryCard from './MemoryCard.vue'
import { Loader2 } from 'lucide-vue-next'

const store = useDashboardStore()
const listRef = ref<HTMLElement | null>(null)

function handleScroll() {
  if (!listRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = listRef.value
  const isNearBottom = scrollTop + clientHeight >= scrollHeight - 200

  if (isNearBottom && !store.isLoading && store.hasMore) {
    store.loadMore()
  }
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <div>
        <span class="font-semibold">Memories</span>
        <span class="text-sm text-gray-500 dark:text-gray-400 ml-2">
          ({{ store.memories.length }}{{ store.hasMore ? '+' : '' }} loaded)
        </span>
      </div>
    </div>

    <!-- Memory List -->
    <div
      ref="listRef"
      @scroll="handleScroll"
      class="overflow-y-auto max-h-[calc(100vh-280px)] p-4 space-y-3"
    >
      <!-- Loading State -->
      <div v-if="store.isLoading && store.memories.length === 0" class="flex items-center justify-center py-12">
        <Loader2 class="w-8 h-8 animate-spin text-blue-600" />
        <span class="ml-2 text-gray-500">Loading memories...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="!store.isLoading && store.memories.length === 0" class="text-center py-12">
        <div class="text-gray-400 text-lg mb-2">No memories found</div>
        <p class="text-gray-500 text-sm">Try adjusting your filters or search query</p>
      </div>

      <!-- Memory Cards -->
      <MemoryCard
        v-for="memory in store.memories"
        :key="memory.id"
        :memory="memory"
        :selected="store.selectedMemory?.id === memory.id"
        :search-term="store.filters.search"
        @click="store.selectMemory(memory)"
      />

      <!-- Load More Indicator -->
      <div v-if="store.isLoading && store.memories.length > 0" class="flex items-center justify-center py-4">
        <Loader2 class="w-5 h-5 animate-spin text-blue-600" />
        <span class="ml-2 text-sm text-gray-500">Loading more...</span>
      </div>

      <!-- End of List -->
      <div v-if="!store.hasMore && store.memories.length > 0" class="text-center py-4 text-sm text-gray-500">
        End of list
      </div>
    </div>
  </div>
</template>
