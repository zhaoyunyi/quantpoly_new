import { defineConfig } from '@tanstack/react-start/config'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
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
    },
    server: {
      fs: {
        allow: [path.resolve(import.meta.dirname, '../../libs')],
      },
    },
  },
})
