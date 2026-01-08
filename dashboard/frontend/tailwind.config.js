/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  safelist: [
    // Memory type background colors
    'bg-type-decision', 'bg-type-solution', 'bg-type-insight', 'bg-type-error',
    'bg-type-context', 'bg-type-preference', 'bg-type-todo', 'bg-type-reference',
    'bg-type-workflow', 'bg-type-api', 'bg-type-other',
    // Memory type text colors
    'text-type-decision', 'text-type-solution', 'text-type-insight', 'text-type-error',
    'text-type-context', 'text-type-preference', 'text-type-todo', 'text-type-reference',
    'text-type-workflow', 'text-type-api', 'text-type-other',
    // Memory type border colors (left border)
    'border-l-type-decision', 'border-l-type-solution', 'border-l-type-insight', 'border-l-type-error',
    'border-l-type-context', 'border-l-type-preference', 'border-l-type-todo', 'border-l-type-reference',
    'border-l-type-workflow', 'border-l-type-api', 'border-l-type-other',
  ],
  theme: {
    extend: {
      colors: {
        // Memory type colors
        'type-decision': '#3b82f6',     // blue
        'type-solution': '#22c55e',     // green
        'type-insight': '#a855f7',      // purple
        'type-error': '#ef4444',        // red
        'type-context': '#f59e0b',      // amber
        'type-preference': '#ec4899',   // pink
        'type-todo': '#06b6d4',         // cyan
        'type-reference': '#6366f1',    // indigo
        'type-workflow': '#14b8a6',     // teal
        'type-api': '#f97316',          // orange
        'type-other': '#64748b',        // slate
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
