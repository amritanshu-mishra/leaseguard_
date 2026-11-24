import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// The browser talks only to same-origin /api. Vite proxies to the FastAPI
// process, so the preview host never needs a localhost URL or CORS exception.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Accept older cached clients that called /api/config etc. as well.
        rewrite: (path) =>
          path.startsWith('/api/v1/') || path === '/api/v1'
            ? path
            : path.replace(/^\/api\//, '/api/v1/'),
      },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist' },
  test: { environment: 'jsdom', globals: true, setupFiles: [] },
});
