/**
 * Landing Page — Hero Section
 *
 * 一句话价值主张 + CTA（注册/登录）
 * 符合 UISpec：理性可信、克制科技感。
 */

import { CtaLink } from "./CtaLink";

export function HeroSection() {
  return (
    <section className="flex-shrink-0 py-2xl px-xl">
      <div className="max-w-[960px] mx-auto text-center flex flex-col items-center gap-lg">
        <h1
          className="text-title-page"
          style={{ fontSize: "36px", lineHeight: 1.15 }}
        >
          可解释的量化分析工具
        </h1>
        <p
          className="text-body-secondary max-w-lg mx-auto"
          style={{ fontSize: "16px", lineHeight: 1.6 }}
        >
          QuantPoly 帮助你构建、回测与监控量化策略。
          <br />
          数据驱动决策，结论优先呈现，每一步都可审计、可解释。
        </p>

        {/* CTA 按钮组 */}
        <div className="flex items-center gap-md mt-sm">
          <CtaLink href="/auth/register" variant="primary" size="lg">
            立即开始
          </CtaLink>
          <CtaLink href="/auth/login" variant="secondary" size="lg">
            已有账号？登录
          </CtaLink>
        </div>
      </div>
    </section>
  );
}
