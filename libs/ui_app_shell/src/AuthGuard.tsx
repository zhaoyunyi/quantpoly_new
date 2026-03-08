/**
 * App Shell — AuthGuard
 *
 * 认证守卫组件。
 * - 进入受保护路由前拉取 GET /users/me
 * - 401 统一跳转 /auth/login?next=...
 */

import { type ReactNode } from "react";
import { useAuth } from "@qp/api-client";
import { Spinner } from "@qp/ui";
import { redirectTo } from "./redirect";

export interface AuthGuardProps {
  children: ReactNode;
  /** 自定义登录路径，默认 /auth/login */
  loginPath?: string;
}

/**
 * 认证守卫。
 * 包裹受保护内容，未登录时重定向到登录页。
 */
export function AuthGuard({
  children,
  loginPath = "/auth/login",
}: AuthGuardProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-page">
        <div className="flex flex-col items-center gap-md">
          <Spinner size="lg" />
          <p className="text-body-secondary">正在验证身份…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // 客户端重定向到登录页
    if (typeof window !== "undefined") {
      const next = encodeURIComponent(
        window.location.pathname + window.location.search,
      );
      redirectTo(`${loginPath}?next=${next}`);
    }
    return null;
  }

  return <>{children}</>;
}
