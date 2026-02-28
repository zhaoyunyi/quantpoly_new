import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return (
    <main className="max-w-[960px] mx-auto px-xl py-2xl">
      <h1 className="text-title-page">QuantPoly 前端（TanStack Start）</h1>
      <p className="text-body-secondary mt-sm">
        当前仅保留前端规范与 Design Tokens 基线，业务 UI 暂未实现。
      </p>
      <p className="text-disclaimer mt-lg">
        免责声明：本页面内容用于开发阶段验证 UI 基线，不构成任何投资建议。
      </p>
    </main>
  )
}
