import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        serif: ['Cormorant Garamond', 'serif'],
      },
      colors: {
        halos: {
          bg: '#0a0a0a',
          surface: '#0f0f0f',
          panel: '#131313',
          border: '#222222',
          line: '#1a1a1a',
          text: '#e8e6df',
          dim: '#8a8a82',
          muted: '#5c5c56',
          faint: '#3a3a36',
          accent: '#48e3ea',
          gold: '#c8a45c',
          warn: '#f5a623',
          error: '#e84848',
          ok: '#6ad08f',
        },
      },
      letterSpacing: {
        widest: '0.22em',
      },
    },
  },
  plugins: [],
} satisfies Config
