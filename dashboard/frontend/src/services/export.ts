import type { Memory } from '@/types'

export function exportToJson(memories: Memory[], filename = 'memories.json') {
  const data = JSON.stringify(memories, null, 2)
  downloadFile(data, filename, 'application/json')
}

export function exportToMarkdown(memories: Memory[], filename = 'memories.md') {
  const lines: string[] = [
    '# Omni-Cortex Memories Export',
    '',
    `Exported: ${new Date().toISOString()}`,
    `Total: ${memories.length} memories`,
    '',
    '---',
    '',
  ]

  for (const memory of memories) {
    lines.push(`## ${memory.memory_type.toUpperCase()} - ${memory.id}`)
    lines.push('')
    lines.push(`**Status:** ${memory.status}`)
    lines.push(`**Importance:** ${memory.importance_score}`)
    lines.push(`**Created:** ${new Date(memory.created_at).toLocaleString()}`)
    if (memory.tags.length > 0) {
      lines.push(`**Tags:** ${memory.tags.join(', ')}`)
    }
    lines.push('')
    lines.push('### Content')
    lines.push('')
    lines.push(memory.content)
    lines.push('')
    if (memory.context) {
      lines.push('### Context')
      lines.push('')
      lines.push(memory.context)
      lines.push('')
    }
    lines.push('---')
    lines.push('')
  }

  downloadFile(lines.join('\n'), filename, 'text/markdown')
}

export function exportSingleMemoryToMarkdown(memory: Memory): string {
  const lines: string[] = [
    `# ${memory.memory_type.toUpperCase()}`,
    '',
    `**ID:** ${memory.id}`,
    `**Status:** ${memory.status}`,
    `**Importance:** ${memory.importance_score}`,
    `**Created:** ${new Date(memory.created_at).toLocaleString()}`,
    `**Last Accessed:** ${memory.last_accessed ? new Date(memory.last_accessed).toLocaleString() : 'Never'}`,
    `**Access Count:** ${memory.access_count}`,
  ]

  if (memory.tags.length > 0) {
    lines.push(`**Tags:** ${memory.tags.join(', ')}`)
  }

  lines.push('')
  lines.push('## Content')
  lines.push('')
  lines.push(memory.content)

  if (memory.context) {
    lines.push('')
    lines.push('## Context')
    lines.push('')
    lines.push(memory.context)
  }

  return lines.join('\n')
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    return false
  }
}
