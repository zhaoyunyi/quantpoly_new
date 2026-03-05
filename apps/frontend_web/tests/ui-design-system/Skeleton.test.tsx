/**
 * UI Design System — Skeleton.test.tsx
 *
 * GIVEN: Skeleton / Spinner / EmptyState 组件
 * WHEN:  渲染
 * THEN:  可访问性属性正确
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Skeleton, Spinner, EmptyState } from "@qp/ui/Skeleton";

describe("Skeleton", () => {
  it("given_default_when_rendered_then_has_status_role", () => {
    render(<Skeleton />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("given_default_when_rendered_then_has_loading_label", () => {
    render(<Skeleton />);
    expect(screen.getByLabelText("加载中")).toBeInTheDocument();
  });
});

describe("Spinner", () => {
  it("given_default_when_rendered_then_has_status_role", () => {
    render(<Spinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("given_size_lg_when_rendered_then_applies_size_class", () => {
    render(<Spinner size="lg" />);
    const el = screen.getByRole("status");
    expect(el.classList.toString()).toContain("h-10");
  });
});

describe("EmptyState", () => {
  it("given_default_when_rendered_then_shows_title", () => {
    render(<EmptyState />);
    expect(screen.getByText("暂无数据")).toBeInTheDocument();
  });

  it("given_custom_title_when_rendered_then_shows_custom", () => {
    render(<EmptyState title="没有策略" description="请先创建一个策略" />);
    expect(screen.getByText("没有策略")).toBeInTheDocument();
    expect(screen.getByText("请先创建一个策略")).toBeInTheDocument();
  });
});
