/**
 * UI Design System — 工具函数
 *
 * cn(): clsx 封装，用于组合 Tailwind 类名。
 */

import { clsx, type ClassValue } from 'clsx'

/**
 * 合并 Tailwind CSS 类名。
 * 支持条件类名、数组、对象语法。
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs)
}

/* ─── 通用样式常量 ─── */

/** 焦点环样式（键盘可达，焦点可见） */
export const focusRingClass =
  'outline-none ring-2 ring-primary-500/40 ring-offset-1'

/** 禁用态基准 */
export const disabledClass = 'opacity-40 cursor-not-allowed pointer-events-none'

/** 过渡动画基准（120ms ease-out） */
export const transitionClass = 'transition-all duration-[120ms] ease-out'
