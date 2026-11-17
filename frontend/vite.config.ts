import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same origin as the page, so the browser sends the session cookie. The Host
    // header must stay unchanged or Django's CSRF origin check rejects every POST.
    proxy: {
      "/auth": { target: "http://127.0.0.1:8000", changeOrigin: false },
      // Proxies "/courses" and everything under it, so no page route may start with it.
      "/courses": { target: "http://127.0.0.1:8000", changeOrigin: false },
      "/progress": { target: "http://127.0.0.1:8000", changeOrigin: false },
    },
  },
})
