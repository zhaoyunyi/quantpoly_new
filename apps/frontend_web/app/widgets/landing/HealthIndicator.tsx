/**
 * Landing Page — Health Indicator
 *
 * 调用 GET /health 展示后端运行状态。
 * 失败不阻断页面——纯增强信息。
 */

import { healthCheck, type HealthResult } from "@qp/api-client";
import { useLoadable } from "../../shared/useLoadable";

export function HealthIndicator() {
  const health = useLoadable<HealthResult>(healthCheck);

  if (health.loading) {
    return (
      <span className="inline-flex items-center gap-xs text-caption text-text-muted">
        <span className="inline-block w-2 h-2 rounded-full bg-secondary-300 animate-pulse" />
        检测中…
      </span>
    );
  }

  if (health.error) {
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
      data-testid="health-ok"
    >
      <span className="inline-block w-2 h-2 rounded-full bg-primary-500" />
      服务运行中
    </span>
  );
}
