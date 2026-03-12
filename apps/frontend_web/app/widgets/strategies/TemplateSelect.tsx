/**
 * 模板选择组件
 *
 * 基于 Select 组件，异步加载模板列表。
 * 支持 loading 态与失败重试。
 */

import { useCallback, useEffect, useState } from "react";
import { Select, Skeleton, Button } from "@qp/ui";
import { getStrategyTemplates } from "@qp/api-client";
import type { StrategyTemplate, AppError } from "@qp/api-client";

export interface TemplateSelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  error?: string;
  className?: string;
}

export function TemplateSelect({
  value,
  onValueChange,
  disabled,
  error,
  className,
}: TemplateSelectProps) {
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const result = await getStrategyTemplates();
      setTemplates(result);
    } catch (err) {
      setLoadError((err as AppError).message || "加载模板失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className={className}>
        <Skeleton width="100%" height="40px" />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={className}>
        <p className="text-caption text-state-risk mb-xs">{loadError}</p>
        <Button variant="ghost" size="sm" onClick={() => void load()}>
          重试
        </Button>
      </div>
    );
  }

  const options = templates.map((t) => ({
    value: t.templateId,
    label: t.name,
  }));

  return (
    <Select
      label="策略模板"
      options={options}
      value={value}
      onValueChange={onValueChange}
      placeholder="请选择策略模板"
      disabled={disabled}
      error={error}
      className={className}
    />
  );
}

export { type StrategyTemplate };
