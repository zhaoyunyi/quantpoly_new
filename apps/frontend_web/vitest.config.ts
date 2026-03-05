import { defineConfig } from 'vitest/config'
import path from 'node:path'

const rootDir = path.resolve(import.meta.dirname, '../..')
const nodeModules = path.resolve(import.meta.dirname, 'node_modules')

export default defineConfig({
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: 'react',
  },
  resolve: {
    alias: {
      '@qp/api-client': path.resolve(rootDir, 'libs/frontend_api_client/src'),
      '@qp/ui': path.resolve(rootDir, 'libs/ui_design_system/src'),
      '@qp/shell': path.resolve(rootDir, 'libs/ui_app_shell/src'),
      // 确保 libs 源码中的裸模块引用解析到 frontend_web 的 node_modules
      'react': path.resolve(nodeModules, 'react'),
      'react-dom': path.resolve(nodeModules, 'react-dom'),
      'react/jsx-runtime': path.resolve(nodeModules, 'react/jsx-runtime'),
      'clsx': path.resolve(nodeModules, 'clsx'),
      '@base-ui/react': path.resolve(nodeModules, '@base-ui/react'),
    },
  },
  server: {
    fs: {
      allow: [rootDir],
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: [
      'tests/**/*.test.{ts,tsx}',
    ],
  },
})
