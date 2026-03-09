import type { RiskAlert } from '@qp/api-client'
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

export interface AlertListProps {
  alerts: RiskAlert[]
  busyAlertId?: string | null
  onAcknowledge?: (alertId: string) => void
  onResolve?: (alertId: string) => void
}

export function AlertList({
  alerts,
  busyAlertId,
  onAcknowledge,
  onResolve,
}: AlertListProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell>级别</TableHeaderCell>
          <TableHeaderCell>规则</TableHeaderCell>
          <TableHeaderCell>内容</TableHeaderCell>
          <TableHeaderCell>状态</TableHeaderCell>
          <TableHeaderCell className="text-right">操作</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {alerts.length === 0 ? (
          <TableEmpty colSpan={5} message="暂无未解决告警" />
        ) : (
          alerts.map((a) => {
            const busy = busyAlertId === a.id
            return (
              <TableRow key={a.id}>
                <TableCell className="font-medium">{a.severity}</TableCell>
                <TableCell className="whitespace-nowrap">{a.ruleName}</TableCell>
                <TableCell className="max-w-[36ch]">
                  <span className="block truncate" title={a.message}>
                    {a.message}
                  </span>
                </TableCell>
                <TableCell className="whitespace-nowrap">{a.status}</TableCell>
                <TableCell className="text-right">
                  <div className="inline-flex items-center gap-xs">
                    {onAcknowledge && (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={busy}
                        loading={busy}
                        onClick={() => onAcknowledge(a.id)}
                      >
                        确认
                      </Button>
                    )}
                    {onResolve && (
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={busy}
                        loading={busy}
                        onClick={() => onResolve(a.id)}
                      >
                        解决
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

