import { onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'

export function useKeyboardShortcuts() {
  const store = useDashboardStore()

  function handleKeydown(e: KeyboardEvent) {
    // Ignore if user is typing in an input
    const target = e.target as HTMLElement
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
      return
    }

    switch (e.key) {
      case '/':
        // Focus search bar
        e.preventDefault()
        const searchInput = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement
        if (searchInput) {
          searchInput.focus()
        }
        break

      case 'Escape':
        // Clear selection or filters
        if (store.selectedMemory) {
          store.clearSelection()
        } else {
          store.resetFilters()
        }
        break

      case 'j':
        // Navigate to next memory
        e.preventDefault()
        navigateMemories(1)
        break

      case 'k':
        // Navigate to previous memory
        e.preventDefault()
        navigateMemories(-1)
        break

      case 'Enter':
        // Open selected memory detail (if not already open)
        if (store.selectedMemory === null && store.memories.length > 0) {
          store.selectMemory(store.memories[0])
        }
        break

      case 'r':
        // Refresh data
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault()
          store.refresh()
        }
        break

      case '?':
        // Show keyboard shortcuts help
        e.preventDefault()
        showShortcutsHelp()
        break
    }

    // Number keys 1-9 for quick type filter
    if (e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.metaKey) {
      const typeIndex = parseInt(e.key) - 1
      const types = ['decision', 'solution', 'insight', 'error', 'context', 'preference', 'todo', 'reference', 'workflow']
      if (typeIndex < types.length) {
        e.preventDefault()
        const currentType = store.filters.memory_type
        if (currentType === types[typeIndex]) {
          store.applyFilters({ memory_type: null })
        } else {
          store.applyFilters({ memory_type: types[typeIndex] })
        }
      }
    }
  }

  function navigateMemories(direction: number) {
    if (store.memories.length === 0) return

    const currentIndex = store.selectedMemory
      ? store.memories.findIndex(m => m.id === store.selectedMemory!.id)
      : -1

    let newIndex = currentIndex + direction
    if (newIndex < 0) newIndex = 0
    if (newIndex >= store.memories.length) newIndex = store.memories.length - 1

    store.selectMemory(store.memories[newIndex])

    // Scroll the selected memory into view
    setTimeout(() => {
      const selectedCard = document.querySelector('[class*="border-blue-500"]')
      if (selectedCard) {
        selectedCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }, 50)
  }

  function showShortcutsHelp() {
    const shortcuts = `
Keyboard Shortcuts:
─────────────────────
/         Focus search
Esc       Clear selection/filters
j/k       Navigate memories
Enter     Select first memory
r         Refresh data
1-9       Filter by type
?         Show this help
    `.trim()

    alert(shortcuts)
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })

  return {
    showShortcutsHelp,
  }
}
