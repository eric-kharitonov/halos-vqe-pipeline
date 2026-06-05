import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        serif: ['Cormorant Garamond', 'serif'],
      },
      colors: {
        halos: {
          bg: '#0a0a0a',
          surface: '#111111',
          border: '#1e1e1e',
          text: '#e8e6df',
          muted: '#666',
          accent: '#48e3ea',
          warn: '#f5a623',
          error: '#e84848',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
