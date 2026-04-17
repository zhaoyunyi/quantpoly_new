/**
 * App Shell — AppShell
 *
 * 已认证用户的主布局。
 * - 固定侧栏导航
 * - 顶部状态栏（右侧服务状态，不含横向菜单）
 * - 内容区（max-w-[1200px] 居中）
 * - 底部免责声明
 */

import { type ReactNode, useEffect, useState } from "react";
import { cn, transitionClass, useTheme } from "@qp/ui";
import { healthCheck, useAuth } from "@qp/api-client";
import { NAV_ITEMS, type NavItem } from "./navigation";
import { redirectTo } from "./redirect";

export interface AppShellProps {
  children: ReactNode;
  /** 当前路由路径，用于高亮侧栏导航项 */
  currentPath?: string;
  /** 顶部状态栏右侧自定义操作区（如通知铃铛） */
  headerActions?: ReactNode;
}

export function AppShell({ children, currentPath = "/", headerActions }: AppShellProps) {
  const { user, logout } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-bg-page flex">
      <aside
        className={cn(
          "fixed top-0 left-0 h-screen bg-bg-card border-r border-secondary-300/20 flex flex-col z-30",
          transitionClass,
          sidebarCollapsed ? "w-16" : "w-56",
        )}
      >
        <div
          className="flex items-center justify-between h-14 px-4 border-b border-secondary-300/20"
          data-testid="shell-sidebar-header"
        >
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
            )}
            aria-label={sidebarCollapsed ? "展开侧栏" : "收起侧栏"}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              data-testid="shell-sidebar-toggle-icon"
              data-icon={sidebarCollapsed ? "expand-sidebar" : "collapse-sidebar"}
              aria-hidden="true"
            >
              <rect
                x="2.75"
                y="3.25"
                width="12.5"
                height="11.5"
                rx="1.5"
                stroke="currentColor"
                strokeWidth="1.4"
              />
              <path
                d="M7.5 3.5v11"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
              />
              {sidebarCollapsed ? (
                <path
                  d="M9.25 7l2 2-2 2"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ) : (
                <path
                  d="M11.25 7l-2 2 2 2"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
            </svg>
          </button>
        </div>

        <nav className="flex-1 py-sm overflow-y-auto">
          <ul className="flex flex-col gap-0.5 px-2">
            {NAV_ITEMS.map((item) => (
              <SidebarNavItem
                key={item.path}
                item={item}
                isActive={currentPath.startsWith(item.path)}
                collapsed={sidebarCollapsed}
                currentPath={currentPath}
              />
            ))}
          </ul>
        </nav>

        {user && (
          <div className="border-t border-secondary-300/20 p-3">
            <div
              className={cn(
                "flex items-center gap-sm",
                sidebarCollapsed && "justify-center",
              )}
            >
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

      <div
        className={cn(
          "flex-1 flex flex-col",
          transitionClass,
          sidebarCollapsed ? "ml-16" : "ml-56",
        )}
      >
        <header className="border-b border-secondary-300/20 bg-bg-card/95 backdrop-blur-sm">
          <div
            className="h-14 w-full max-w-[1200px] mx-auto px-xl flex items-center justify-end gap-sm"
            data-testid="shell-top-status"
          >
            {headerActions}
            <ThemeToggle />
            <ShellHealthIndicator />
          </div>
        </header>

        <main className="flex-1 w-full max-w-[1200px] mx-auto px-xl py-lg">
          {children}
        </main>

        <footer className="py-md px-xl text-center border-t border-secondary-300/10">
          <p className="text-disclaimer">
            不构成投资建议。回测结果不代表未来表现。
          </p>
        </footer>
      </div>
    </div>
  );
}

function SidebarNavItem({
  item,
  isActive,
  collapsed,
  currentPath,
}: {
  item: NavItem;
  isActive: boolean;
  collapsed: boolean;
  currentPath: string;
}) {
  return (
    <li>
      <a
        href={item.path}
        onClick={(event) => {
          event.preventDefault();
          redirectTo(item.path);
        }}
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
      {!collapsed && isActive && item.children && (
        <ul className="mt-0.5 flex flex-col gap-0.5">
          {item.children.map((child) => (
            <li key={child.path}>
              <a
                href={child.path}
                onClick={(event) => {
                  event.preventDefault();
                  redirectTo(child.path);
                }}
                className={cn(
                  "block pl-10 pr-3 py-1.5 rounded-sm text-caption",
                  transitionClass,
                  currentPath === child.path
                    ? "text-primary-700 font-medium"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-subtle",
                )}
              >
                {child.label}
              </a>
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

function ThemeToggle() {
  const { resolved, setTheme } = useTheme();
  const isDark = resolved === "dark";
  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "p-1.5 rounded-sm text-text-muted hover:text-text-primary hover:bg-bg-subtle",
        transitionClass,
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40",
      )}
      aria-label={isDark ? "切换到浅色模式" : "切换到深色模式"}
    >
      {isDark ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}

function ShellHealthIndicator() {
  const [status, setStatus] = useState<"loading" | "ok" | "down">("loading");

  useEffect(() => {
    let cancelled = false;
    void healthCheck()
      .then(() => {
        if (cancelled) return;
        setStatus("ok");
      })
      .catch(() => {
        if (cancelled) return;
        setStatus("down");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <span className="inline-flex items-center gap-xs text-caption text-text-muted">
        <span className="inline-block w-2 h-2 rounded-full bg-secondary-300 animate-pulse" />
        检测中…
      </span>
    );
  }

  if (status === "down") {
    return (
      <span className="inline-flex items-center gap-xs text-caption text-text-muted">
        <span className="inline-block w-2 h-2 rounded-full bg-secondary-500" />
        服务暂不可用
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-xs text-caption text-text-muted"
      data-testid="shell-health-ok"
    >
      <span className="inline-block w-2 h-2 rounded-full bg-primary-500" />
      服务运行中
    </span>
  );
}
