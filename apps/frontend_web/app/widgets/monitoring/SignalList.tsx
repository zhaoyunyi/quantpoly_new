import type { TradingSignal } from '@qp/api-client'
import {
  Button,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  TableEmpty,
} from '@qp/ui'

export interface SignalListProps {
  signals: TradingSignal[]
  busySignalId?: string | null
  selectedSignalIds?: string[]
  onToggleSignal?: (signalId: string, selected: boolean) => void
  onToggleAllSignals?: (selected: boolean) => void
  onProcess?: (signalId: string) => void
  onExecute?: (signalId: string) => void
  onCancel?: (signalId: string) => void
}

export function SignalList({
  signals,
  busySignalId,
  selectedSignalIds = [],
  onToggleSignal,
  onToggleAllSignals,
  onProcess,
  onExecute,
  onCancel,
}: SignalListProps) {
  const selected = new Set(selectedSignalIds)
  const allSelected = signals.length > 0 && signals.every((item) => selected.has(item.id))

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell className="w-[44px]">
            <input
              type="checkbox"
              aria-label="选择全部信号"
              checked={allSelected}
              disabled={signals.length === 0}
              onChange={(event) => onToggleAllSignals?.(event.currentTarget.checked)}
            />
          </TableHeaderCell>
          <TableHeaderCell>标的</TableHeaderCell>
          <TableHeaderCell>方向</TableHeaderCell>
          <TableHeaderCell>状态</TableHeaderCell>
          <TableHeaderCell className="text-right">操作</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {signals.length === 0 ? (
          <TableEmpty colSpan={5} message="暂无待处理信号" />
        ) : (
          signals.map((s) => {
            const busy = busySignalId === s.id
            return (
              <TableRow key={s.id}>
                <TableCell>
                  <input
                    type="checkbox"
                    aria-label={`选择信号 ${s.symbol}`}
                    checked={selected.has(s.id)}
                    onChange={(event) => onToggleSignal?.(s.id, event.currentTarget.checked)}
                  />
                </TableCell>
                <TableCell className="font-medium">{s.symbol}</TableCell>
                <TableCell>{s.side}</TableCell>
                <TableCell>{s.status}</TableCell>
                <TableCell className="text-right">
                  <div className="inline-flex items-center gap-xs">
                    {onProcess && (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busy}
                        loading={busy}
                        onClick={() => onProcess(s.id)}
                      >
                        处理
                      </Button>
                    )}
                    {onExecute && (
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={busy}
                        loading={busy}
                        onClick={() => onExecute(s.id)}
                      >
                        执行
                      </Button>
                    )}
                    {onCancel && (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busy}
                        loading={busy}
                        onClick={() => onCancel(s.id)}
                      >
                        取消
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )
          })
        )}
      </TableBody>
    </Table>
  )
}
