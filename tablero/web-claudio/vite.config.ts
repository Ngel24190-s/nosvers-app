import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// PWA Claudio (007) — bundle separado del cockpit (`tablero/web/`).
// Servida bajo claudio.72.61.160.108.nip.io (vhost Caddy dedicado).
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          motion: ['framer-motion'],
          icons: ['lucide-react'],
        },
      },
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/voz/api': 'http://localhost:8766',
      '/tablero/api': 'http://localhost:8766',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
