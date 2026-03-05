/**
 * App Shell — AppShell
 *
 * 已认证用户的主布局。
 * - 固定侧栏导航（一级 IA 对齐 spec/UISpec.md 8.1）
 * - 顶栏（品牌 + 用户信息）
 * - 内容区（max-w-[1200px] 居中）
 * - 底部免责声明
 *
 * 全部样式来自 Design Tokens。
 */

import { type ReactNode, useState } from "react";
import { cn, transitionClass } from "@qp/ui";
import { useAuth } from "@qp/api-client";
import { NAV_ITEMS, type NavItem } from "./navigation";

export interface AppShellProps {
  children: ReactNode;
  /** 当前路由路径，用于高亮导航项 */
  currentPath?: string;
}

export function AppShell({ children, currentPath = "/" }: AppShellProps) {
  const { user, logout } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-bg-page flex">
      {/* ─── 侧栏 ─── */}
      <aside
        className={cn(
          "fixed top-0 left-0 h-screen bg-bg-card border-r border-secondary-300/20 flex flex-col z-30",
          transitionClass,
          sidebarCollapsed ? "w-16" : "w-56",
        )}
      >
        {/* 品牌标识 */}
        <div className="flex items-center h-14 px-4 border-b border-secondary-300/20">
          <span
            className={cn(
              "text-title-card text-primary-900 font-medium whitespace-nowrap overflow-hidden",
              transitionClass,
              sidebarCollapsed && "opacity-0 w-0",
            )}
          >
            QuantPoly
          </span>
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className={cn(
              "p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-bg-subtle",
              transitionClass,
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40",
              sidebarCollapsed && "mx-auto",
            )}
            aria-label={sidebarCollapsed ? "展开侧栏" : "收起侧栏"}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              aria-hidden="true"
            >
              {sidebarCollapsed ? (
                <path
                  d="M6 4l5 5-5 5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ) : (
                <path
                  d="M12 4L7 9l5 5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
            </svg>
          </button>
        </div>

        {/* 导航列表 */}
        <nav className="flex-1 py-sm overflow-y-auto">
          <ul className="flex flex-col gap-0.5 px-2">
            {NAV_ITEMS.map((item) => (
              <SidebarNavItem
                key={item.path}
                item={item}
                isActive={currentPath.startsWith(item.path)}
                collapsed={sidebarCollapsed}
              />
            ))}
          </ul>
        </nav>

        {/* 底部用户区 */}
        {user && (
          <div className="border-t border-secondary-300/20 p-3">
            <div
              className={cn(
                "flex items-center gap-sm",
                sidebarCollapsed && "justify-center",
              )}
            >
              {/* 头像占位 */}
              <div className="shrink-0 w-8 h-8 rounded-full bg-primary-500/10 flex items-center justify-center text-primary-700 text-caption font-medium">
                {user.displayName?.[0]?.toUpperCase() ||
                  user.email[0]?.toUpperCase()}
              </div>
              {!sidebarCollapsed && (
                <div className="flex-1 min-w-0">
                  <p className="text-body font-medium truncate">
                    {user.displayName}
                  </p>
                  <button
                    type="button"
                    onClick={() => logout()}
                    className="text-caption text-text-muted hover:text-state-risk transition-colors"
                  >
                    退出登录
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </aside>

      {/* ─── 主内容区 ─── */}
      <div
        className={cn(
          "flex-1 flex flex-col",
          transitionClass,
          sidebarCollapsed ? "ml-16" : "ml-56",
        )}
      >
        {/* 内容 */}
        <main className="flex-1 w-full max-w-[1200px] mx-auto px-xl py-lg">
          {children}
        </main>

        {/* 免责声明 */}
        <footer className="py-md px-xl text-center border-t border-secondary-300/10">
          <p className="text-disclaimer">
            不构成投资建议。回测结果不代表未来表现。
          </p>
        </footer>
      </div>
    </div>
  );
}

/* ─── 侧栏导航项 ─── */

function SidebarNavItem({
  item,
  isActive,
  collapsed,
}: {
  item: NavItem;
  isActive: boolean;
  collapsed: boolean;
}) {
  return (
    <li>
      <a
        href={item.path}
        className={cn(
          "flex items-center gap-sm px-3 py-2 rounded-sm text-body select-none",
          transitionClass,
          isActive
            ? "bg-primary-500/10 text-primary-700 font-medium"
            : "text-text-secondary hover:bg-bg-subtle hover:text-text-primary",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40",
          collapsed && "justify-center px-2",
        )}
        aria-current={isActive ? "page" : undefined}
        title={collapsed ? item.label : undefined}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          className="shrink-0"
          aria-hidden="true"
        >
          {item.icon}
        </svg>
        {!collapsed && <span className="truncate">{item.label}</span>}
      </a>
    </li>
  );
}
