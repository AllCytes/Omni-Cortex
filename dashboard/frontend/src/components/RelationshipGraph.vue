<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import { getRelationshipGraph, type GraphNode, type GraphEdge } from '@/services/api'
import * as d3 from 'd3'
import { GitBranch, ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-vue-next'

interface D3Node extends GraphNode, d3.SimulationNodeDatum {
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  type: string
  strength: number
}

const store = useDashboardStore()
const containerRef = ref<HTMLDivElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const nodes = ref<D3Node[]>([])
const links = ref<D3Link[]>([])
const selectedNode = ref<D3Node | null>(null)
const zoomLevel = ref(1)

let simulation: d3.Simulation<D3Node, D3Link> | null = null
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let zoom: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null

// Type colors matching the app's theme
const typeColors: Record<string, string> = {
  decision: '#3b82f6', // blue
  solution: '#22c55e', // green
  insight: '#8b5cf6', // purple
  error: '#ef4444', // red
  context: '#06b6d4', // cyan
  preference: '#f97316', // orange
  todo: '#eab308', // yellow
  reference: '#64748b', // slate
  workflow: '#ec4899', // pink
  api: '#14b8a6', // teal
  other: '#9ca3af', // gray
}

// Edge styles based on relationship type
function getEdgeStyle(type: string): { stroke: string; dasharray: string } {
  switch (type) {
    case 'related_to':
      return { stroke: '#6b7280', dasharray: 'none' }
    case 'supersedes':
      return { stroke: '#f59e0b', dasharray: '8,4' }
    case 'derived_from':
      return { stroke: '#8b5cf6', dasharray: '4,4' }
    case 'contradicts':
      return { stroke: '#ef4444', dasharray: '2,2' }
    default:
      return { stroke: '#6b7280', dasharray: 'none' }
  }
}

async function loadData(centerId?: string) {
  if (!store.currentProject) return

  loading.value = true
  error.value = null

  try {
    const graph = await getRelationshipGraph(store.currentProject.db_path, centerId, 2)

    if (graph.nodes.length === 0) {
      nodes.value = []
      links.value = []
      return
    }

    nodes.value = graph.nodes.map(n => ({ ...n }))
    links.value = graph.edges.map(e => ({
      source: e.source,
      target: e.target,
      type: e.type,
      strength: e.strength,
    }))

    renderGraph()
  } catch (e) {
    error.value = 'Failed to load relationship data'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!svgRef.value || !containerRef.value) return

  // Clear previous graph
  d3.select(svgRef.value).selectAll('*').remove()

  if (nodes.value.length === 0) return

  const width = containerRef.value.clientWidth
  const height = 500

  // Create SVG
  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height])

  // Add zoom behavior
  zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
      zoomLevel.value = event.transform.k
    })

  svg.call(zoom)

  // Main group for zoom/pan
  const g = svg.append('g')

  // Arrow markers for directed edges
  svg.append('defs').selectAll('marker')
    .data(['related_to', 'supersedes', 'derived_from', 'contradicts'])
    .join('marker')
    .attr('id', d => `arrow-${d}`)
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', d => getEdgeStyle(d).stroke)

  // Create force simulation
  simulation = d3.forceSimulation<D3Node>(nodes.value)
    .force('link', d3.forceLink<D3Node, D3Link>(links.value)
      .id(d => d.id)
      .distance(100)
      .strength(d => d.strength * 0.5))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(30))

  // Draw links
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links.value)
    .join('line')
    .attr('stroke', d => getEdgeStyle(d.type).stroke)
    .attr('stroke-width', d => Math.max(1, d.strength * 3))
    .attr('stroke-dasharray', d => getEdgeStyle(d.type).dasharray)
    .attr('marker-end', d => `url(#arrow-${d.type})`)

  // Draw nodes
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes.value)
    .join('g')
    .attr('cursor', 'pointer')
    .call(d3.drag<SVGGElement, D3Node>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
    .on('click', (event, d) => handleNodeClick(d))
    .on('dblclick', (event, d) => handleNodeDoubleClick(d))

  // Node circles
  node.append('circle')
    .attr('r', 15)
    .attr('fill', d => typeColors[d.type] || typeColors.other)
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)

  // Node labels
  node.append('text')
    .attr('dy', 30)
    .attr('text-anchor', 'middle')
    .attr('fill', document.documentElement.classList.contains('dark') ? '#d1d5db' : '#374151')
    .attr('font-size', '10px')
    .text(d => d.content.substring(0, 20) + (d.content.length > 20 ? '...' : ''))

  // Tooltip
  node.append('title')
    .text(d => `${d.type}: ${d.content}`)

  // Update positions on tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => (d.source as D3Node).x!)
      .attr('y1', d => (d.source as D3Node).y!)
      .attr('x2', d => (d.target as D3Node).x!)
      .attr('y2', d => (d.target as D3Node).y!)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })
}

function dragstarted(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
  if (!event.active) simulation?.alphaTarget(0.3).restart()
  event.subject.fx = event.subject.x
  event.subject.fy = event.subject.y
}

function dragged(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
  event.subject.fx = event.x
  event.subject.fy = event.y
}

function dragended(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
  if (!event.active) simulation?.alphaTarget(0)
  event.subject.fx = null
  event.subject.fy = null
}

function handleNodeClick(node: D3Node) {
  selectedNode.value = node
  // Select the memory in the store
  const memory = store.memories.find(m => m.id === node.id)
  if (memory) {
    store.selectMemory(memory)
  }
}

function handleNodeDoubleClick(node: D3Node) {
  // Recenter the graph on this node
  loadData(node.id)
}

function zoomIn() {
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.scaleBy, 1.3)
  }
}

function zoomOut() {
  if (svg && zoom) {
    svg.transition().duration(300).call(zoom.scaleBy, 0.7)
  }
}

function resetZoom() {
  if (svg && zoom && containerRef.value) {
    const width = containerRef.value.clientWidth
    const height = 500
    svg.transition().duration(300).call(
      zoom.transform,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(1).translate(-width / 2, -height / 2)
    )
  }
}

function refresh() {
  loadData()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', renderGraph)
})

onUnmounted(() => {
  simulation?.stop()
  window.removeEventListener('resize', renderGraph)
})

watch(() => store.currentProject, () => loadData())
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <GitBranch class="w-5 h-5 text-purple-500" />
        Memory Relationships
      </h2>
      <div class="flex items-center gap-2">
        <button
          @click="zoomOut"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut class="w-4 h-4" />
        </button>
        <span class="text-sm text-gray-500">{{ Math.round(zoomLevel * 100) }}%</span>
        <button
          @click="zoomIn"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Zoom In"
        >
          <ZoomIn class="w-4 h-4" />
        </button>
        <button
          @click="resetZoom"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Reset View"
        >
          <Maximize2 class="w-4 h-4" />
        </button>
        <button
          @click="refresh"
          :disabled="loading"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Refresh"
        >
          <RefreshCw :class="['w-4 h-4', loading && 'animate-spin']" />
        </button>
      </div>
    </div>

    <!-- Legend -->
    <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex flex-wrap gap-4 text-xs">
      <span class="text-gray-500">Nodes:</span>
      <span v-for="(color, type) in typeColors" :key="type" class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: color }"></span>
        {{ type }}
      </span>
    </div>
    <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex flex-wrap gap-4 text-xs">
      <span class="text-gray-500">Edges:</span>
      <span class="flex items-center gap-1">
        <span class="w-6 border-t-2 border-gray-500"></span>
        related_to
      </span>
      <span class="flex items-center gap-1">
        <span class="w-6 border-t-2 border-amber-500 border-dashed"></span>
        supersedes
      </span>
      <span class="flex items-center gap-1">
        <span class="w-6 border-t-2 border-purple-500 border-dotted"></span>
        derived_from
      </span>
      <span class="flex items-center gap-1">
        <span class="w-6 border-t-2 border-red-500" style="border-style: dotted;"></span>
        contradicts
      </span>
    </div>

    <!-- Graph Container -->
    <div ref="containerRef" class="relative min-h-[500px]">
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-50/50 dark:bg-gray-800/50">
        <div class="animate-pulse text-gray-500">Loading graph...</div>
      </div>

      <div v-else-if="error" class="absolute inset-0 flex items-center justify-center">
        <div class="text-red-500">{{ error }}</div>
      </div>

      <div v-else-if="nodes.length === 0" class="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
        <GitBranch class="w-12 h-12 mb-2 opacity-50" />
        <p class="font-medium">No Relationships Found</p>
        <p class="text-sm">Link memories using the cortex_link_memories tool to see connections here.</p>
      </div>

      <svg ref="svgRef" class="w-full"></svg>
    </div>

    <!-- Selected Node Info -->
    <div
      v-if="selectedNode"
      class="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50"
    >
      <div class="flex items-start gap-3">
        <span
          class="px-2 py-1 rounded text-xs font-medium capitalize"
          :style="{ backgroundColor: typeColors[selectedNode.type] + '20', color: typeColors[selectedNode.type] }"
        >
          {{ selectedNode.type }}
        </span>
        <p class="text-sm text-gray-700 dark:text-gray-300 flex-1">
          {{ selectedNode.content }}
        </p>
      </div>
      <p class="mt-2 text-xs text-gray-500">
        Double-click a node to recenter the graph on that memory.
      </p>
    </div>
  </div>
</template>
