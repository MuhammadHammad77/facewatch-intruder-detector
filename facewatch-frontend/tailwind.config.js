/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0a0e1a',
        'bg-card': '#111827',
        'bg-elevated': '#1f2937',
        'border-color': '#374151',
        'accent-green': '#10b981',
        'accent-red': '#ef4444',
        'accent-blue': '#3b82f6',
      }
    },
  },
  plugins: [],
}
