import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      clientPort: 3000,
    },
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  resolve: {
    extensions: ['.js', '.jsx']
  }
})