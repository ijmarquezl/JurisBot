import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Your backend server address
        changeOrigin: true,
        // NOTE: no `rewrite` here. The backend serves routes under the /api
        // prefix (include_router(prefix="/api")), so the prefix must be kept
        // when forwarding to the backend, matching the production nginx config.
      },
    },
  },
})