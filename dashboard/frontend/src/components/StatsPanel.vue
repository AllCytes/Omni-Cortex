<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { TYPE_COLORS } from '@/types'
import { Database, Tag, TrendingUp, Eye, Layers } from 'lucide-vue-next'
import ActivityHeatmap from '@/components/charts/ActivityHeatmap.vue'
import ToolUsageChart from '@/components/charts/ToolUsageChart.vue'
import MemoryGrowthChart from '@/components/charts/MemoryGrowthChart.vue'
import CommandUsageChart from '@/components/charts/CommandUsageChart.vue'
import SkillUsageChart from '@/components/charts/SkillUsageChart.vue'
import MCPUsageChart from '@/components/charts/MCPUsageChart.vue'

const store = useDashboardStore()

const typeData = computed(() => {
  if (!store.stats) return []
  const total = store.stats.total_count || 1
  return Object.entries(store.stats.by_type)
    .map(([type, count]) => ({
      type,
      count,
      percentage: Math.round((count / total) * 100),
      color: TYPE_COLORS[type] || 'bg-gray-500'
    }))
    .sort((a, b) => b.count - a.count)
})

const statusData = computed(() => {
  if (!store.stats) return []
  const total = store.stats.total_count || 1
  return Object.entries(store.stats.by_status)
    .map(([status, count]) => ({
      status,
      count,
      percentage: Math.round((count / total) * 100)
    }))
    .sort((a, b) => b.count - a.count)
})

const topTags = computed(() => {
  return store.tags.slice(0, 15)
})

function getStatusColor(status: string): string {
  switch (status) {
    case 'fresh': return 'bg-green-500'
    case 'needs_review': return 'bg-yellow-500'
    case 'outdated': return 'bg-red-500'
    case 'archived': return 'bg-gray-500'
    default: return 'bg-gray-500'
  }
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Multi-Project Indicator -->
    <div
      v-if="store.isMultiProject"
      class="lg:col-span-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/30 rounded-lg p-4 border border-blue-200 dark:border-blue-800"
    >
      <div class="flex items-center gap-2 mb-2">
        <Layers class="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <span class="font-semibold text-blue-900 dark:text-blue-100">
          Viewing {{ store.selectedProjects.length }} Projects (Combined)
        </span>
      </div>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="project in store.selectedProjects"
          :key="project.db_path"
          class="px-3 py-1 bg-white dark:bg-gray-800 rounded-full text-sm font-medium text-gray-700 dark:text-gray-300 shadow-sm"
        >
          {{ project.display_name || project.name }}
        </span>
      </div>
    </div>

    <!-- Overview Card -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
        <Database class="w-5 h-5 text-blue-500" />
        Overview
      </h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <span class="text-gray-600 dark:text-gray-400">Total Memories</span>
          <span class="text-2xl font-bold">{{ store.stats?.total_count ?? 0 }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-600 dark:text-gray-400">Avg. Importance</span>
          <span class="text-2xl font-bold">{{ store.stats?.avg_importance ?? 0 }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-gray-600 dark:text-gray-400">Total Views</span>
          <span class="text-2xl font-bold">{{ store.stats?.total_access_count ?? 0 }}</span>
        </div>
      </div>
    </div>

    <!-- Type Distribution -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
        <TrendingUp class="w-5 h-5 text-purple-500" />
        By Type
      </h2>
      <div class="space-y-3">
        <div v-for="item in typeData" :key="item.type" class="flex items-center gap-3">
          <div class="w-20 text-sm capitalize truncate">{{ item.type }}</div>
          <div class="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              :class="['h-full rounded-full', item.color]"
              :style="{ width: `${item.percentage}%` }"
            ></div>
          </div>
          <div class="w-12 text-right text-sm text-gray-600 dark:text-gray-400">
            {{ item.count }}
          </div>
        </div>
      </div>
    </div>

    <!-- Status Distribution -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
        <Eye class="w-5 h-5 text-green-500" />
        By Status
      </h2>
      <div class="space-y-3">
        <div v-for="item in statusData" :key="item.status" class="flex items-center gap-3">
          <div class="w-28 text-sm capitalize truncate">{{ item.status.replace('_', ' ') }}</div>
          <div class="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              :class="['h-full rounded-full', getStatusColor(item.status)]"
              :style="{ width: `${item.percentage}%` }"
            ></div>
          </div>
          <div class="w-12 text-right text-sm text-gray-600 dark:text-gray-400">
            {{ item.count }}
          </div>
        </div>
      </div>
    </div>

    <!-- Top Tags -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 md:col-span-2 lg:col-span-3">
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
        <Tag class="w-5 h-5 text-orange-500" />
        Top Tags
      </h2>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="tag in topTags"
          :key="tag.name"
          class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-full text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors cursor-pointer"
          @click="store.applyFilters({ tags: [tag.name] })"
        >
          {{ tag.name }}
          <span class="ml-1 text-gray-500 dark:text-gray-400">({{ tag.count }})</span>
        </span>
      </div>
    </div>

    <!-- Charts Section -->
    <ActivityHeatmap class="lg:col-span-3" />
    <ToolUsageChart />
    <MemoryGrowthChart class="md:col-span-2" />

    <!-- Command Analytics Section -->
    <CommandUsageChart />
    <SkillUsageChart />
    <MCPUsageChart />
  </div>
</template>
