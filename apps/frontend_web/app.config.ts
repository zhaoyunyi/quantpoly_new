import { defineConfig } from '@tanstack/react-start/config'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
    build: {
      rollupOptions: {
        output: {
          // TanStack Start 在生成 tsr routes manifest 时会读取入口 chunk 的 `imports`。
          // 当前依赖组合下，若产物被打成单 chunk，会导致 `imports` 缺失并触发 SSR 构建报错。
          // 这里显式拆分 vendor，确保入口 chunk 持有 imports 元数据。
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
