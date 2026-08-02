import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    host: true,
    allowedHosts: true,
    hmr: {
      protocol: 'wss',
      host: 'fairy-comfort-controversial-exclusion.trycloudflare.com',
      clientPort: 443,
    },
  },
})