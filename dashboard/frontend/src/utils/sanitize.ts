import DOMPurify from 'dompurify'

/**
 * Sanitize HTML content to prevent XSS attacks.
 * Allows safe HTML tags while removing dangerous ones.
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote',
      'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'span', 'div', 'mark'
    ],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel', 'data-memory-index'],
    ALLOW_DATA_ATTR: false,
    ADD_ATTR: ['target'], // Allow target="_blank" for links
  })
}

/**
 * Sanitize markdown-rendered HTML for safe display.
 */
export function sanitizeMarkdown(html: string): string {
  return sanitizeHtml(html)
}
