/**
 * Highlight search terms in text by wrapping them in <mark> tags
 */
export function highlightText(text: string, searchTerm: string): string {
  if (!searchTerm || !text) return escapeHtml(text)

  const escaped = escapeHtml(text)
  const searchEscaped = escapeRegExp(searchTerm)

  // Case-insensitive global replacement
  const regex = new RegExp(`(${searchEscaped})`, 'gi')
  return escaped.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-700 px-0.5 rounded">$1</mark>')
}

/**
 * Escape HTML special characters to prevent XSS
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Escape special regex characters
 */
function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Truncate text and preserve highlighting
 */
export function truncateWithHighlight(
  text: string,
  searchTerm: string,
  maxLength: number = 200
): string {
  if (!text) return ''

  // If there's a search term, try to show context around it
  if (searchTerm) {
    const lowerText = text.toLowerCase()
    const lowerSearch = searchTerm.toLowerCase()
    const index = lowerText.indexOf(lowerSearch)

    if (index !== -1) {
      // Calculate start position to center the search term
      const contextStart = Math.max(0, index - Math.floor(maxLength / 3))
      const contextEnd = Math.min(text.length, contextStart + maxLength)

      let truncated = text.substring(contextStart, contextEnd)

      // Add ellipsis if truncated
      if (contextStart > 0) truncated = '...' + truncated
      if (contextEnd < text.length) truncated = truncated + '...'

      return highlightText(truncated, searchTerm)
    }
  }

  // No search term or not found, just truncate
  if (text.length <= maxLength) {
    return highlightText(text, searchTerm)
  }

  return highlightText(text.substring(0, maxLength) + '...', searchTerm)
}
