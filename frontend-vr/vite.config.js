export default {
    server: {
      host: '0.0.0.0',
      port: process.env.FRONTEND_VR_PORT,
      proxy: {
        '/api': {
          target: process.env.BACKEND_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }  