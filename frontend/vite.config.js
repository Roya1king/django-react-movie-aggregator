import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // --- THIS IS THE FIX ---
  // Tell Vite to build all asset paths starting with /static/
  base: '/static/'
  // --- END FIX ---
})
