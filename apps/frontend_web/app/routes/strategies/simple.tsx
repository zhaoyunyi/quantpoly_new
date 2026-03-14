/**
 * /strategies/simple — 向导式创建策略
 *
 * 三步骤向导：
 * 1. 选择模板
 * 2. 配置参数
 * 3. 确认预览 + 创建提交
 *
 * 创建后可选"立即回测"，成功后跳转策略详情页。
 */

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState, type ChangeEvent } from "react";

import { ProtectedLayout } from "../../entry_wiring";
import {
  getStrategyTemplates,
  createStrategyFromTemplate,
  createBacktestForStrategy,
} from "@qp/api-client";
import type { StrategyTemplate, StrategyItem, AppError } from "@qp/api-client";
import { Button, TextField, Skeleton, useToast } from "@qp/ui";
import { WizardStepper } from "../../widgets/strategies/WizardStepper";

export const Route = createFileRoute("/strategies/simple")({
  component: StrategySimplePage,
});

const WIZARD_STEPS = [
  { label: "选择模板" },
  { label: "配置参数" },
  { label: "确认创建" },
];

export function StrategySimplePage() {
  const navigate = useNavigate();
  const toast = useToast();

  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);

  // Step1: 选择模板
  const [selectedTemplateId, setSelectedTemplateId] = useState("");

  // Step2: 参数
  const [name, setName] = useState("");
  const [params, setParams] = useState<Record<string, string>>({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Step3: 创建
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<StrategyItem | null>(null);
  const [btLoading, setBtLoading] = useState(false);

  const loadTemplates = useCallback(async () => {
    setLoadingTemplates(true);
    try {
      const tpls = await getStrategyTemplates();
      setTemplates(tpls);
    } catch {
      toast.show("加载模板失败", "error");
    } finally {
      setLoadingTemplates(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  const selectedTemplate = templates.find(
    (t) => t.templateId === selectedTemplateId,
  );

  const handleSelectTemplate = (id: string) => {
    setSelectedTemplateId(id);
    // 用默认值初始化参数
    const tpl = templates.find((t) => t.templateId === id);
    if (tpl?.defaults) {
      const init: Record<string, string> = {};
      for (const [k, v] of Object.entries(tpl.defaults)) {
        init[k] = String(v);
      }
      setParams(init);
    }
    setFieldErrors({});
    setStep(1);
  };

  const handleParamChange = (key: string, value: string) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleGoToConfirm = () => {
    if (!name.trim()) {
      setFieldErrors({ name: "请输入策略名称" });
      return;
    }
    setFieldErrors({});
    setStep(2);
  };

  const handleCreate = async () => {
    setCreating(true);
    setFieldErrors({});
    try {
      const numericParams: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(params)) {
        const num = Number(v);
        numericParams[k] = Number.isNaN(num) ? v : num;
      }
      const result = await createStrategyFromTemplate({
        name: name.trim(),
        templateId: selectedTemplateId,
        parameters: numericParams,
      });
      setCreated(result);
      toast.show("策略创建成功！", "success");
    } catch (err) {
      const appErr = err as AppError;
      if (appErr.kind === "validation") {
        const msg = appErr.message || "";
        const fieldMatch = msg.match(/parameter[:\s]+(\w+)/i);
        if (fieldMatch) {
          setFieldErrors({ [fieldMatch[1]]: msg });
        } else {
          setFieldErrors({ name: msg });
        }
        setStep(1); // 回到参数步骤
      } else {
        toast.show(appErr.message || "创建失败", "error");
      }
    } finally {
      setCreating(false);
    }
  };

  const handleRunBacktest = async () => {
    if (!created) return;
    setBtLoading(true);
    try {
      await createBacktestForStrategy(created.id, { config: {} });
      toast.show("回测已开始", "success");
      void navigate({ to: "/strategies/$id", params: { id: created.id } });
    } catch (err) {
      toast.show((err as AppError).message || "创建回测失败", "error");
    } finally {
      setBtLoading(false);
    }
  };

  return (
    <ProtectedLayout>
      <div className="flex flex-col gap-lg max-w-2xl mx-auto">
        {/* 标题 */}
        <header>
          <button
            type="button"
            className="text-primary-500 hover:text-primary-700 text-body transition-all duration-120 ease-out"
            onClick={() => void navigate({ to: "/strategies" })}
          >
            ← 返回策略列表
          </button>
          <h1 className="text-title-page mt-xs">向导式创建策略</h1>
          <p className="text-body-secondary mt-xs">
            通过三个简单步骤快速创建量化策略。
          </p>
        </header>

        {/* 步进器 */}
        <WizardStepper steps={WIZARD_STEPS} currentStep={created ? 3 : step} />

        {/* Step 1: 选择模板 */}
        {step === 0 && !created && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">选择策略模板</h2>
            {loadingTemplates ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
                {Array.from({ length: 4 }).map((_, idx) => (
                  <Skeleton key={idx} width="100%" height="80px" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
                {templates.map((tpl) => (
                  <button
                    key={tpl.templateId}
                    type="button"
                    onClick={() => handleSelectTemplate(tpl.templateId)}
                    className={`flex flex-col gap-xs p-md rounded-md border text-left transition-all duration-120 ease-out hover:opacity-92 ${
                      selectedTemplateId === tpl.templateId
                        ? "border-primary-500 bg-primary-500/5"
                        : "border-secondary-300/20 hover:border-secondary-300/40"
                    }`}
                  >
                    <span className="text-body font-medium text-text-primary">
                      {tpl.name}
                    </span>
                    <span className="text-caption text-text-muted">
                      参数: {Object.keys(tpl.requiredParameters).join(", ")}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Step 2: 配置参数 */}
        {step === 1 && !created && selectedTemplate && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">
              配置参数 — {selectedTemplate.name}
            </h2>
            <div className="flex flex-col gap-md">
              <TextField
                label="策略名称"
                value={name}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setName(e.target.value)
                }
                placeholder="输入策略名称"
                error={fieldErrors["name"]}
              />
              {Object.entries(selectedTemplate.requiredParameters).map(
                ([key, rule]) => (
                  <TextField
                    key={key}
                    label={key}
                    value={params[key] ?? ""}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleParamChange(key, e.target.value)
                    }
                    type="number"
                    error={fieldErrors[key]}
                    help={`类型: ${rule.type}${rule.min !== undefined ? ` · 最小: ${rule.min}` : ""}${rule.max !== undefined ? ` · 最大: ${rule.max}` : ""}`}
                    placeholder={
                      selectedTemplate.defaults?.[key] !== undefined
                        ? `默认: ${selectedTemplate.defaults[key]}`
                        : undefined
                    }
                  />
                ),
              )}
              <div className="flex justify-between mt-sm">
                <Button variant="secondary" onClick={() => setStep(0)}>
                  上一步
                </Button>
                <Button onClick={handleGoToConfirm} disabled={!name.trim()}>
                  下一步
                </Button>
              </div>
            </div>
          </section>
        )}

        {/* Step 3: 确认预览 */}
        {step === 2 && !created && selectedTemplate && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">确认创建</h2>
            <div className="flex flex-col gap-sm">
              <div className="flex gap-md">
                <span className="text-caption text-text-secondary w-24">
                  名称
                </span>
                <span className="text-body font-medium">{name}</span>
              </div>
              <div className="flex gap-md">
                <span className="text-caption text-text-secondary w-24">
                  模板
                </span>
                <span className="text-body">{selectedTemplate.name}</span>
              </div>
              {Object.entries(params).map(([key, val]) => (
                <div key={key} className="flex gap-md">
                  <span className="text-caption text-text-secondary w-24">
                    {key}
                  </span>
                  <span className="text-data-mono">{val}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-lg">
              <Button variant="secondary" onClick={() => setStep(1)}>
                上一步
              </Button>
              <Button loading={creating} onClick={() => void handleCreate()}>
                确认创建
              </Button>
            </div>
          </section>
        )}

        {/* 创建成功 */}
        {created && (
          <section className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg">
            <h2 className="text-title-section mb-md">🎉 创建成功</h2>
            <p className="text-body mb-md">
              策略「{created.name}」已成功创建（ID: {created.id}）。
            </p>
            <div className="flex gap-sm">
              <Button
                onClick={() =>
                  void navigate({
                    to: "/strategies/$id",
                    params: { id: created.id },
                  })
                }
              >
                查看详情
              </Button>
              <Button
                variant="secondary"
                loading={btLoading}
                onClick={() => void handleRunBacktest()}
              >
                立即回测
              </Button>
              <Button
                variant="ghost"
                onClick={() => void navigate({ to: "/strategies" })}
              >
                返回列表
              </Button>
            </div>
          </section>
        )}

        {/* 免责声明 */}
        <footer className="text-disclaimer text-text-muted mt-lg">
          不构成投资建议。回测结果不代表未来表现。
        </footer>
      </div>
    </ProtectedLayout>
  );
}
