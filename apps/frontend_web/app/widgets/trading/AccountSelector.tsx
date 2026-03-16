/**
 * AccountSelector — 交易账户下拉选择器
 *
 * 异步加载账户列表，支持选中回调。
 */

import { useCallback, useEffect, useState } from "react";

import { getTradingAccounts } from "@qp/api-client";
import type { TradingAccount } from "@qp/api-client";
import { Select, Skeleton, useToast } from "@qp/ui";

export interface AccountSelectorProps {
  value: string;
  onValueChange: (accountId: string) => void;
  className?: string;
}

export function AccountSelector({
  value,
  onValueChange,
  className,
}: AccountSelectorProps) {
  const toast = useToast();
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getTradingAccounts();
      setAccounts(data);
    } catch {
      toast.show("加载账户失败", "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return <Skeleton width="200px" height="40px" />;
  }

  const options = accounts.map((a) => ({
    value: a.id,
    label: `${a.accountName}${a.isActive ? "" : "（已停用）"}`,
  }));

  return (
    <Select
      label="交易账户"
      options={options}
      value={value}
      onValueChange={onValueChange}
      placeholder="选择账户"
      className={className}
    />
  );
}
