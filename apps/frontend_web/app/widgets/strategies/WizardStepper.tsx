/**
 * 向导步进器组件
 *
 * 用于 /strategies/simple 向导式创建流程。
 * 展示步骤进度（步骤号 + 标签 + 连线）。
 */

import { cn, transitionClass } from "@qp/ui";

export interface WizardStep {
  label: string;
}

export interface WizardStepperProps {
  steps: WizardStep[];
  currentStep: number;
  className?: string;
}

export function WizardStepper({
  steps,
  currentStep,
  className,
}: WizardStepperProps) {
  return (
    <nav
      aria-label="创建向导步骤"
      className={cn("flex items-center gap-xs", className)}
    >
      {steps.map((step, idx) => {
        const isActive = idx === currentStep;
        const isCompleted = idx < currentStep;

        return (
          <div key={step.label} className="flex items-center gap-xs">
            {/* 步骤圆圈 */}
            <div
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-full text-[length:var(--text-caption)] font-medium",
                transitionClass,
                isCompleted
                  ? "bg-primary-700 text-text-on-primary"
                  : isActive
                    ? "bg-primary-500 text-text-on-primary"
                    : "bg-bg-subtle text-text-muted",
              )}
              aria-current={isActive ? "step" : undefined}
            >
              {isCompleted ? (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M3 8l4 4 6-6"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                idx + 1
              )}
            </div>
            {/* 标签 */}
            <span
              className={cn(
                "text-caption whitespace-nowrap",
                isActive || isCompleted
                  ? "text-text-primary font-medium"
                  : "text-text-muted",
              )}
            >
              {step.label}
            </span>
            {/* 连线 */}
            {idx < steps.length - 1 && (
              <div
                className={cn(
                  "h-px w-8",
                  isCompleted ? "bg-primary-700" : "bg-secondary-300/30",
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
