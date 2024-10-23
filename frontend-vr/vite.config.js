export default {
    server: {
      host: '0.0.0.0',
      port: 3001,
      proxy: {
        '/api': {
          target: process.env.BACKEND_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }  