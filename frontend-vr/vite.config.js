export default {
    server: {
      host: '0.0.0.0',
      port: 3001,
      proxy: {
        '/api': {
          target: 'http://backend:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }  