import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: process.env.FRONTEND_PC_PORT,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})