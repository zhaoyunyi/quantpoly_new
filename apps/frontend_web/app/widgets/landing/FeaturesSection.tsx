/**
 * Landing Page — Features Section
 *
 * 策略/回测/风控/监控四大核心能力展示。
 * 不堆砌视觉效果，克制呈现。
 */

import { Ruler, BarChart3, ShieldCheck, Radio, type LucideIcon } from 'lucide-react'

interface FeatureItem {
  title: string;
  description: string;
  icon: LucideIcon;
}

const FEATURES: FeatureItem[] = [
  {
    title: "策略管理",
    description:
      "构建、版本化与追踪你的量化策略，完整记录每一次变更与决策依据。",
    icon: Ruler,
  },
  {
    title: "回测引擎",
    description:
      "基于历史数据验证策略表现，提供收益率、回撤、胜率等核心指标分析。",
    icon: BarChart3,
  },
  {
    title: "风控中心",
    description: "实时告警与多维度风险监控，让异常暴露在造成损失之前。",
    icon: ShieldCheck,
  },
  {
    title: "实时监控",
    description: "聚合信号、任务与账户状态，一目了然掌握全局运行态势。",
    icon: Radio,
  },
];

function FeatureCard({ title, description, icon: Icon }: FeatureItem) {
  return (
    <div className="bg-bg-card rounded-md shadow-card border border-secondary-300/20 p-lg flex flex-col gap-sm">
      <div className="flex items-center gap-sm">
        <Icon className="size-6 text-primary-700 shrink-0" aria-hidden="true" />
        <h3 className="text-title-card">{title}</h3>
      </div>
      <p className="text-body-secondary">{description}</p>
    </div>
  );
}

export function FeaturesSection() {
  return (
    <section className="flex-1 px-xl py-2xl bg-bg-subtle" aria-label="核心能力">
      <div className="max-w-[960px] mx-auto">
        <h2 className="text-title-section text-center">核心能力</h2>
        <p className="text-body-secondary text-center mt-xs max-w-lg mx-auto">
          四大模块覆盖量化工作流全链路，克制而可靠。
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-md mt-lg">
          {FEATURES.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </div>
    </section>
  );
}
