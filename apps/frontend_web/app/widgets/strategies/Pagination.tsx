/**
 * 分页组件
 *
 * 显示页码和翻页按钮。
 * 对齐后端 page/pageSize 参数规范（page 从 1 开始）。
 */

import { Button } from "@qp/ui";

export interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  return (
    <div className="flex items-center justify-between gap-md">
      <span className="text-caption text-text-muted">
        共 {total} 条 · 第 {page}/{totalPages} 页
      </span>
      <div className="inline-flex items-center gap-xs">
        <Button
          variant="secondary"
          size="sm"
          disabled={!hasPrev}
          onClick={() => onPageChange(page - 1)}
        >
          上一页
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={!hasNext}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </Button>
      </div>
    </div>
  );
}
