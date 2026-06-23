import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/benefit-compass/',   // GitHub Pages 프로젝트 경로
  server: {
    proxy: { '/api': 'http://localhost:8080' }
  }
})
