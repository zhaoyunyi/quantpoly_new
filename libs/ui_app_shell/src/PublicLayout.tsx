/**
 * App Shell — PublicLayout
 *
 * 公开页面布局（登录/注册等），不含侧栏导航。
 * 居中卡片式布局，品牌标识 + 免责声明。
 */

import { type ReactNode } from "react";
import { cn } from "@qp/ui";

export interface PublicLayoutProps {
  children: ReactNode;
  className?: string;
}

export function PublicLayout({ children, className }: PublicLayoutProps) {
  return (
    <div className="min-h-screen bg-bg-page flex flex-col">
      {/* 顶部品牌栏 */}
      <header className="flex items-center h-14 px-xl border-b border-secondary-300/20 bg-bg-card">
        <a href="/" className="flex items-center gap-sm">
          <span className="text-title-card text-primary-900 font-medium">
            QuantPoly
          </span>
        </a>
      </header>

      {/* 内容区：居中卡片 */}
      <main
        className={cn(
          "flex-1 flex items-center justify-center px-md py-2xl",
          className,
        )}
      >
        <div className="w-full max-w-md">{children}</div>
      </main>

      {/* 底部免责声明 */}
      <footer className="py-md px-xl text-center">
        <p className="text-disclaimer">
          不构成投资建议。回测结果不代表未来表现。
        </p>
      </footer>
    </div>
  );
}
