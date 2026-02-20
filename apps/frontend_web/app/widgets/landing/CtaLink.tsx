import type { AnchorHTMLAttributes } from "react";
import { cn, focusRingClass, transitionClass } from "@qp/ui";

type CtaLinkVariant = "primary" | "secondary" | "ghost";
type CtaLinkSize = "sm" | "lg";

interface CtaLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  variant?: CtaLinkVariant;
  size?: CtaLinkSize;
}

const variantStyles: Record<CtaLinkVariant, string> = {
  primary: "bg-primary-700 text-white hover:opacity-92 active:bg-primary-900",
  secondary:
    "bg-bg-subtle text-text-primary border border-secondary-300/40 hover:opacity-92 active:bg-bg-page",
  ghost:
    "bg-transparent text-primary-700 hover:bg-bg-subtle hover:opacity-92 active:bg-bg-subtle",
};

const sizeStyles: Record<CtaLinkSize, string> = {
  sm: "h-8 px-3 text-caption gap-1.5",
  lg: "h-12 px-6 text-body gap-2.5 font-medium",
};

const focusVisibleClass = focusRingClass
  .split(" ")
  .map((token) => `focus-visible:${token}`)
  .join(" ");

export function CtaLink({
  variant = "primary",
  size = "sm",
  className,
  ...props
}: CtaLinkProps) {
  return (
    <a
      className={cn(
        "inline-flex items-center justify-center font-medium select-none rounded-sm",
        transitionClass,
        focusVisibleClass,
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      {...props}
    />
  );
}
