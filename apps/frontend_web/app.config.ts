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
        // 确保 libs 源码中的裸模块引用解析到 frontend_web 的 node_modules
        react: path.resolve(import.meta.dirname, 'node_modules/react'),
        'react-dom': path.resolve(import.meta.dirname, 'node_modules/react-dom'),
        'react/jsx-runtime': path.resolve(import.meta.dirname, 'node_modules/react/jsx-runtime'),
        clsx: path.resolve(import.meta.dirname, 'node_modules/clsx'),
        '@base-ui/react': path.resolve(import.meta.dirname, 'node_modules/@base-ui/react'),
      },
    },
    server: {
      fs: {
        allow: [path.resolve(import.meta.dirname, '../../libs')],
      },
    },
  },
})
