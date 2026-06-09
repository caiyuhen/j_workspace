import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
<<<<<<< HEAD
<<<<<<< HEAD
    port: 5779,
    proxy: {
      '/api': {
        target: 'http://localhost:3666',
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
        changeOrigin: true,
      },
    },
  },
})
