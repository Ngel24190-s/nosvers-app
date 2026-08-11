import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// Audit Chantier QSE — D.I. Environnement
// La build produit UN SEUL fichier `dist/index.html`, autonome (JS + CSS inlinés),
// que l'on partage par WhatsApp / e-mail et qui fonctionne hors connexion.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    target: 'es2020',
    assetsInlineLimit: 100_000_000,
    cssCodeSplit: false,
    reportCompressedSize: false,
    rollupOptions: {
      output: { inlineDynamicImports: true },
    },
  },
  server: { port: 5180 },
});
