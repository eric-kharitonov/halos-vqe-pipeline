import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Backend owns the /api prefix (same as production), so no rewrite/strip here.
    proxy: {
      '/api': { target: 'http://localhost:8000' },
    },
  },
})
