import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  plugins: [
    tanstackStart({
      srcDirectory: 'app',
      router: {
        routesDirectory: 'routes',
        generatedRouteTree: 'routeTree.gen.ts',
      },
    }),
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
  },
  resolve: {
    alias: {
      '@qp/api-client': path.resolve(
        import.meta.dirname,
        '../../libs/frontend_api_client/src',
      ),
      '@qp/ui': path.resolve(
        import.meta.dirname,
        '../../libs/ui_design_system/src',
      ),
      '@qp/shell': path.resolve(
        import.meta.dirname,
        '../../libs/ui_app_shell/src',
      ),
    },
    dedupe: ['react', 'react-dom', 'clsx', '@base-ui/react'],
  },
  server: {
    fs: {
      allow: [
        path.resolve(import.meta.dirname),
        path.resolve(import.meta.dirname, '../../libs'),
      ],
    },
  },
  preview: {
    allowedHosts: ['localhost', '127.0.0.1', 'quantpoly.com', 'www.quantpoly.com'],
  },
})
