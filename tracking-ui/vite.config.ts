import { defineConfig } from 'vite'
import yaml from '@rollup/plugin-yaml'

export default defineConfig({
  plugins: [yaml()],
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      external: ['html2canvas'],
      output: {
        globals: {
          html2canvas: 'html2canvas'
        }
      }
    }
  }
})
