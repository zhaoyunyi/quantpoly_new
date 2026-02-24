import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRoute,
} from "@tanstack/react-router";
import type { ReactNode } from "react";

/// <reference types="vite/client" />
import appCss from "../styles/app.css?url";

import {
  AppProviders,
  bootstrapApiClient,
  type InitialAuthState,
} from "../entry_wiring";

export {
  normalizeBackendOrigin,
  bootstrapApiClient,
  AppProviders,
  ProtectedLayout,
} from "../entry_wiring";

// 入口统一配置：API client baseUrl（直连后端）
bootstrapApiClient();

const UNRESOLVED_AUTH: InitialAuthState = {
  user: null,
  resolved: false,
};

export const Route = createRootRoute({
  loader: async () => {
    // 当前阶段统一走客户端鉴权刷新，避免将 server-only 依赖打入浏览器构建。
    return { initialAuth: { ...UNRESOLVED_AUTH } };
  },
  head: () => ({
    meta: [
      {
        charSet: "utf-8",
      },
      {
        name: "viewport",
        content: "width=device-width, initial-scale=1",
      },
      {
        title: "QuantPoly · 可解释的量化分析工具",
      },
    ],
    links: [
      {
        rel: "preconnect",
        href: "https://fonts.googleapis.com",
      },
      {
        rel: "preconnect",
        href: "https://fonts.gstatic.com",
        crossOrigin: "anonymous",
      },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap",
      },
      {
        rel: "stylesheet",
        href: appCss,
      },
    ],
  }),
  component: RootComponent,
});

function RootComponent() {
  const { initialAuth } = Route.useLoaderData();

  return (
    <RootDocument>
      <AppProviders initialAuth={initialAuth}>
        <Outlet />
      </AppProviders>
    </RootDocument>
  );
}

function RootDocument({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-CN">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}
