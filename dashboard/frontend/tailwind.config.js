/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
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
  plugins: [],
}
