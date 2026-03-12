/**
 * 策略表单组件
 *
 * 支持创建和编辑模式。
 * 字段由策略模板驱动（template → requiredParameters）。
 * 状态：readonly / edit
 */

import { useEffect, useId, useMemo, useState } from "react";
import { TextField, Button } from "@qp/ui";
import type { StrategyTemplate, StrategyItem } from "@qp/api-client";

export interface StrategyFormData {
  name: string;
  template: string;
  parameters: Record<string, string>;
}

export interface StrategyFormProps {
  /** 模板列表（用于驱动参数字段） */
  templates: StrategyTemplate[];
  /** 初始值（编辑模式下传入） */
  initialValues?: Partial<StrategyItem>;
  /** 是否只读 */
  readonly?: boolean;
  /** 提交回调 */
  onSubmit?: (data: StrategyFormData) => void;
  /** 提交中 */
  loading?: boolean;
  /** 字段级别错误映射 */
  fieldErrors?: Record<string, string>;
  /** 选定的模板 ID（外部控制时使用） */
  selectedTemplate?: string;
  /** 模板变更 */
  onTemplateChange?: (templateId: string) => void;
}

export function StrategyForm({
  templates,
  initialValues,
  readonly = false,
  onSubmit,
  loading = false,
  fieldErrors = {},
  selectedTemplate,
  onTemplateChange,
}: StrategyFormProps) {
  const templateSelectId = useId();
  const templateErrorId = `${templateSelectId}-error`;

  const [name, setName] = useState(initialValues?.name ?? "");
  const [template, setTemplate] = useState(
    selectedTemplate ?? initialValues?.template ?? "",
  );
  const [params, setParams] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {};
    if (initialValues?.parameters) {
      for (const [k, v] of Object.entries(initialValues.parameters)) {
        init[k] = String(v);
      }
    }
    return init;
  });

  // initialValues 来源于异步加载；若不做同步，表单在切换策略/保存后可能展示旧值。
  // 同时利用 readonly 切换来实现“取消编辑”时回滚到最新 initialValues。
  useEffect(() => {
    if (!initialValues) return;
    setName(initialValues.name ?? "");
    setTemplate(selectedTemplate ?? initialValues.template ?? "");
    const next: Record<string, string> = {};
    if (initialValues.parameters) {
      for (const [k, v] of Object.entries(initialValues.parameters)) {
        next[k] = String(v);
      }
    }
    setParams(next);
  }, [initialValues?.id, initialValues?.updatedAt, readonly, selectedTemplate]);

  const currentTemplate = useMemo(
    () => templates.find((t) => t.templateId === template),
    [templates, template],
  );

  const handleTemplateChange = (val: string) => {
    setTemplate(val);
    onTemplateChange?.(val);
    // 用默认值初始化参数
    const tpl = templates.find((t) => t.templateId === val);
    if (tpl?.defaults) {
      const next: Record<string, string> = {};
      for (const [k, v] of Object.entries(tpl.defaults)) {
        next[k] = String(v);
      }
      setParams(next);
    }
  };

  const handleParamChange = (key: string, value: string) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.({ name, template, parameters: params });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-md">
      <TextField
        label="策略名称"
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={readonly || loading}
        error={fieldErrors["name"]}
        placeholder="输入策略名称"
      />

      {/* 模板选择（编辑模式下不可更换） */}
      {!initialValues?.template ? (
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor={templateSelectId}
            className="text-body font-medium text-text-primary"
          >
            策略模板
          </label>
          <select
            id={templateSelectId}
            value={template}
            onChange={(e) => handleTemplateChange(e.target.value)}
            disabled={readonly || loading}
            aria-invalid={!!fieldErrors["template"]}
            aria-describedby={
              fieldErrors["template"] ? templateErrorId : undefined
            }
            className="h-10 px-3 bg-bg-card border border-secondary-300/40 rounded-sm text-body text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-500/40 focus:ring-offset-1 transition-all duration-[120ms] ease-out disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <option value="">请选择模板</option>
            {templates.map((t) => (
              <option key={t.templateId} value={t.templateId}>
                {t.name}
              </option>
            ))}
          </select>
          {fieldErrors["template"] && (
            <p
              id={templateErrorId}
              className="text-caption text-state-risk"
              role="alert"
            >
              {fieldErrors["template"]}
            </p>
          )}
        </div>
      ) : (
        <TextField
          label="策略模板"
          value={
            templates.find((t) => t.templateId === initialValues.template)
              ?.name ?? initialValues.template
          }
          disabled
        />
      )}

      {/* 动态参数字段 */}
      {currentTemplate &&
        Object.entries(currentTemplate.requiredParameters).map(
          ([key, rule]) => (
            <TextField
              key={key}
              label={key}
              value={params[key] ?? ""}
              onChange={(e) => handleParamChange(key, e.target.value)}
              disabled={readonly || loading}
              error={fieldErrors[key]}
              help={`类型: ${rule.type}${rule.min !== undefined ? ` · 最小: ${rule.min}` : ""}${rule.max !== undefined ? ` · 最大: ${rule.max}` : ""}`}
              type="number"
              placeholder={
                currentTemplate.defaults?.[key] !== undefined
                  ? `默认: ${currentTemplate.defaults[key]}`
                  : undefined
              }
            />
          ),
        )}

      {!readonly && (
        <div className="flex justify-end gap-sm mt-sm">
          <Button type="submit" loading={loading} disabled={!name || !template}>
            {initialValues?.id ? "保存修改" : "创建策略"}
          </Button>
        </div>
      )}
    </form>
  );
}
