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
      // libs 源码位于 workspace 根目录之外（../libs），需要 dedupe 强制从本项目 node_modules 解析依赖，
      // 否则 SSR dev 下会从 libs 的父目录向上找 node_modules 导致找不到包。
      dedupe: ['react', 'react-dom', 'clsx', '@base-ui/react'],
    },
    server: {
      fs: {
        allow: [path.resolve(import.meta.dirname, '../../libs')],
      },
    },
  },
})
