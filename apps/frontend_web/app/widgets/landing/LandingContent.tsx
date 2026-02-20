/**
 * Landing Page — LandingPage Widget
 *
 * 编排 Hero / Features / Health / 免责声明。
 * 作为 Public 页面，不需要 AuthGuard。
 */

import { HeroSection } from "./HeroSection";
import { FeaturesSection } from "./FeaturesSection";
import { HealthIndicator } from "./HealthIndicator";
import { CtaLink } from "./CtaLink";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-page flex flex-col">
      {/* 顶部导航栏 */}
      <header className="flex items-center justify-between h-14 px-xl border-b border-secondary-300/20 bg-bg-card">
        <a href="/" className="flex items-center gap-sm">
          <span className="text-title-card text-primary-900 font-medium">
            QuantPoly
          </span>
        </a>
        <nav className="flex items-center gap-md">
          <HealthIndicator />
          <CtaLink href="/auth/login" variant="ghost" size="sm">
            登录
          </CtaLink>
          <CtaLink href="/auth/register" variant="primary" size="sm">
            免费注册
          </CtaLink>
        </nav>
      </header>

      {/* Hero */}
      <HeroSection />

      {/* Features */}
      <FeaturesSection />

      {/* 风险提示 + 免责声明 */}
      <footer className="py-lg px-xl bg-bg-page border-t border-secondary-300/20">
        <div className="max-w-[960px] mx-auto text-center flex flex-col gap-sm">
          <p className="text-body-secondary" style={{ fontSize: "13px" }}>
            量化交易存在风险，策略的历史表现不代表未来收益。请根据自身风险承受能力审慎决策。
          </p>
          <p className="text-disclaimer" data-testid="disclaimer">
            免责声明：本平台及其内容不构成任何投资建议。回测结果基于历史数据，不代表未来表现。
          </p>
        </div>
      </footer>
    </div>
  );
}
