"""交易账户应用服务。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from platform_core.uow import NoopUnitOfWork, SnapshotUnitOfWork, UnitOfWork
from trading_account.domain import (
    CashFlow,
    InvalidTradeOrderTransitionError,
    Position,
    TradeOrder,
    TradeRecord,
    TradingAccount,
)
from trading_account.repository import InMemoryTradingAccountRepository


class AccountAccessDeniedError(PermissionError):
    """访问不属于当前用户的账户。"""


class OrderNotFoundError(LookupError):
    """订单不存在。"""


class TradeNotFoundError(LookupError):
    """成交记录不存在。"""


class InsufficientFundsError(ValueError):
    """可用资金不足。"""


class LedgerTransactionError(RuntimeError):
    """账本事务失败。"""


class TradingAdminRequiredError(PermissionError):
    """交易运维接口需要管理员权限。"""


class PriceRefreshConflictError(RuntimeError):
    """价格刷新幂等键冲突。"""


class RiskAssessmentPendingError(RuntimeError):
    """风险评估快照尚未生成。"""


class RiskAssessmentUnavailableError(RuntimeError):
    """风险评估能力未接线。"""


def _default_uow_factory(repository: Any) -> Callable[[], UnitOfWork]:
    if hasattr(repository, "snapshot_state") and hasattr(repository, "restore_state"):
        return lambda: SnapshotUnitOfWork(
            snapshot=repository.snapshot_state,
            restore=repository.restore_state,
        )
    return NoopUnitOfWork


class TradingAccountService:
    def __init__(
        self,
        *,
        repository: InMemoryTradingAccountRepository,
        uow_factory: Callable[[], UnitOfWork] | None = None,
        governance_checker: Callable[..., Any] | None = None,
        risk_snapshot_reader: Callable[..., Any] | None = None,
        risk_evaluator: Callable[..., Any] | None = None,
    ) -> None:
        self._repository = repository
        self._uow_factory = uow_factory or _default_uow_factory(repository)
        self._governance_checker = governance_checker
        self._risk_snapshot_reader = risk_snapshot_reader
        self._risk_evaluator = risk_evaluator
        self._refresh_records: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}

    def create_account(
        self,
        *,
        user_id: str,
        account_name: str,
        initial_capital: float = 0.0,
    ) -> TradingAccount:
        account = TradingAccount.create(user_id=user_id, account_name=account_name)
        self._repository.save_account(account)
        if initial_capital > 0:
            self.deposit(user_id=user_id, account_id=account.id, amount=initial_capital)
        return account

    def list_accounts(self, *, user_id: str) -> list[TradingAccount]:
        return self._repository.list_accounts(user_id=user_id)

    def get_account(self, *, user_id: str, account_id: str) -> TradingAccount | None:
        return self._repository.get_account(account_id=account_id, user_id=user_id)

    def update_account(
        self,
        *,
        user_id: str,
        account_id: str,
        account_name: str | None = None,
        is_active: bool | None = None,
    ) -> TradingAccount | None:
        account = self._repository.get_account(account_id=account_id, user_id=user_id)
        if account is None:
            return None

        if account_name is not None:
            account.account_name = account_name
        if is_active is not None:
            account.is_active = bool(is_active)

        self._repository.save_account(account)
        return account

    @staticmethod
    def _range_stats(values: list[float]) -> dict[str, float | None] | None:
        if not values:
            return None
        return {
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
        }

    def account_filter_config(self, *, user_id: str) -> dict[str, Any]:
        accounts = self.list_accounts(user_id=user_id)

        total_assets_values: list[float] = []
        profit_loss_values: list[float] = []
        profit_loss_rate_values: list[float] = []
        status_counts: dict[str, int] = {"active": 0, "inactive": 0}
        risk_level_counts: dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "UNKNOWN": 0}
        has_positions_count = 0

        for account in accounts:
            cash_balance = self.cash_balance(user_id=user_id, account_id=account.id)
            position_summary = self.position_summary(user_id=user_id, account_id=account.id)
            risk_metrics = self.account_risk_metrics(user_id=user_id, account_id=account.id)

            total_market_value = float(position_summary.get("totalMarketValue", 0.0))
            unrealized_pnl = float(position_summary.get("unrealizedPnl", 0.0))
            unrealized_pnl_ratio = float(position_summary.get("unrealizedPnlRatio", 0.0))

            total_assets_values.append(cash_balance + total_market_value)
            profit_loss_values.append(unrealized_pnl)
            profit_loss_rate_values.append(unrealized_pnl_ratio)

            if float(position_summary.get("positionCount", 0)) > 0:
                has_positions_count += 1

            status_key = "active" if account.is_active else "inactive"
            status_counts[status_key] = status_counts.get(status_key, 0) + 1

            risk_level = str(risk_metrics.get("riskLevel", "UNKNOWN")).upper()
            if risk_level not in risk_level_counts:
                risk_level_counts[risk_level] = 0
            risk_level_counts[risk_level] += 1

        return {
            "totalAccounts": len(accounts),
            "totalAssets": self._range_stats(total_assets_values),
            "profitLoss": self._range_stats(profit_loss_values),
            "profitLossRate": self._range_stats(profit_loss_rate_values),
            "accountTypeCounts": {"paper": len(accounts)},
            "statusCounts": status_counts,
            "riskLevelCounts": risk_level_counts,
            "hasPositionsCount": has_positions_count,
            "hasFrozenBalanceCount": 0,
        }

    def account_summary(self, *, user_id: str, account_id: str) -> dict[str, Any]:
        account = self._repository.get_account(account_id=account_id, user_id=user_id)
        if account is None:
            raise AccountAccessDeniedError("无权访问该账户")

        positions = self.list_positions(user_id=user_id, account_id=account_id)
        position_summary = self.position_summary(user_id=user_id, account_id=account_id)
        stats = self.trade_stats(user_id=user_id, account_id=account_id)

        return {
            "account": account,
            "positions": positions,
            "positionCount": len(positions),
            "totalReturnRatio": float(position_summary.get("unrealizedPnlRatio", 0.0)),
            "stats": stats,
        }

    def cash_flow_summary(self, *, user_id: str, account_id: str) -> dict[str, Any]:
        flows = self.list_cash_flows(user_id=user_id, account_id=account_id)
        total_inflow = sum(item.amount for item in flows if item.amount > 0)
        total_outflow = sum(-item.amount for item in flows if item.amount < 0)
        latest_flow_at = max((item.created_at for item in flows), default=None)

        return {
            "flowCount": len(flows),
            "totalInflow": total_inflow,
            "totalOutflow": total_outflow,
            "netFlow": total_inflow - total_outflow,
            "latestFlowAt": latest_flow_at.isoformat() if latest_flow_at else None,
        }

    def _call_risk_callback(self, callback: Callable[..., Any] | None, **kwargs: Any) -> Any:
        if callback is None:
            raise RiskAssessmentUnavailableError("risk assessment callback is not configured")

        try:
            return callback(**kwargs)
        except TypeError:
            return callback(kwargs["user_id"], kwargs["account_id"])

    def get_risk_assessment(self, *, user_id: str, account_id: str) -> Any:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        snapshot = self._call_risk_callback(
            self._risk_snapshot_reader,
            user_id=user_id,
            account_id=account_id,
        )
        if snapshot is None:
            raise RiskAssessmentPendingError("risk assessment snapshot is pending")
        return snapshot

    def evaluate_risk_assessment(self, *, user_id: str, account_id: str) -> Any:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._call_risk_callback(
            self._risk_evaluator,
            user_id=user_id,
            account_id=account_id,
        )

    def _assert_account_owner(self, *, user_id: str, account_id: str) -> None:
        account = self._repository.get_account(account_id=account_id, user_id=user_id)
        if account is None:
            raise AccountAccessDeniedError("无权访问该账户")

    @staticmethod
    def _to_risk_level(*, score: float) -> str:
        if score >= 70:
            return "high"
        if score >= 30:
            return "medium"
        return "low"

    @staticmethod
    def _refresh_fingerprint(*, price_updates: dict[str, float], account_id: str | None) -> str:
        account_text = account_id or "*"
        pairs = [f"{symbol}:{price}" for symbol, price in sorted(price_updates.items())]
        return f"{account_text}|{'|'.join(pairs)}"

    def upsert_position(
        self,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        quantity: float,
        avg_price: float,
        last_price: float,
    ) -> Position:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        position = Position.create(
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
            last_price=last_price,
        )
        self._repository.save_position(position)
        return position

    def list_positions(self, *, user_id: str, account_id: str) -> list[Position]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_positions(account_id=account_id, user_id=user_id)

    def submit_order(
        self,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> TradeOrder:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        order = TradeOrder.create(
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
        )
        self._repository.save_order(order)
        return order

    def get_order(self, *, user_id: str, account_id: str, order_id: str) -> TradeOrder | None:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.get_order(account_id=account_id, user_id=user_id, order_id=order_id)

    def list_orders(self, *, user_id: str, account_id: str) -> list[TradeOrder]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_orders(account_id=account_id, user_id=user_id)

    def _transition_order_or_raise(
        self,
        *,
        user_id: str,
        account_id: str,
        order_id: str,
        from_status: str,
        to_status: str,
    ) -> TradeOrder:
        existing = self._repository.get_order(account_id=account_id, user_id=user_id, order_id=order_id)
        if existing is None:
            raise OrderNotFoundError("order not found")

        transitioned = self._repository.transition_order_status(
            account_id=account_id,
            user_id=user_id,
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
        )
        if transitioned is None:
            raise InvalidTradeOrderTransitionError(
                f"invalid transition: {existing.status} -> {to_status}"
            )
        return transitioned

    def fill_order(self, *, user_id: str, account_id: str, order_id: str) -> TradeOrder:
        self._assert_account_owner(user_id=user_id, account_id=account_id)

        deferred_transition_error: InvalidTradeOrderTransitionError | None = None
        filled_order: TradeOrder | None = None

        try:
            with self._uow_factory() as uow:
                try:
                    filled_order = self._transition_order_or_raise(
                        user_id=user_id,
                        account_id=account_id,
                        order_id=order_id,
                        from_status="pending",
                        to_status="filled",
                    )
                except InvalidTradeOrderTransitionError as exc:
                    deferred_transition_error = exc
                    uow.commit()
                    filled_order = None

                if deferred_transition_error is not None:
                    return self._raise_transition_error(deferred_transition_error)

                trade = TradeRecord.create(
                    user_id=filled_order.user_id,
                    account_id=filled_order.account_id,
                    symbol=filled_order.symbol,
                    side=filled_order.side,
                    quantity=filled_order.quantity,
                    price=filled_order.price,
                    order_id=filled_order.id,
                )

                notional = filled_order.quantity * filled_order.price
                signed_amount = -notional if filled_order.side == "BUY" else notional
                flow = CashFlow.create(
                    user_id=filled_order.user_id,
                    account_id=filled_order.account_id,
                    amount=signed_amount,
                    flow_type=f"trade_{filled_order.side.lower()}",
                    related_trade_id=trade.id,
                )

                self._repository.save_trade(trade)
                self._repository.save_cash_flow(flow)

            if filled_order is None:
                raise RuntimeError("filled order missing")
            return filled_order
        except (AccountAccessDeniedError, OrderNotFoundError, InvalidTradeOrderTransitionError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise LedgerTransactionError("ledger transaction failed") from exc

    @staticmethod
    def _raise_transition_error(exc: InvalidTradeOrderTransitionError) -> None:
        raise exc

    def cancel_order(self, *, user_id: str, account_id: str, order_id: str) -> TradeOrder:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._transition_order_or_raise(
            user_id=user_id,
            account_id=account_id,
            order_id=order_id,
            from_status="pending",
            to_status="cancelled",
        )

    def record_trade(
        self,
        *,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> TradeRecord:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        trade = TradeRecord.create(
            user_id=user_id,
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
        )
        self._repository.save_trade(trade)
        return trade

    def get_trade(self, *, user_id: str, account_id: str, trade_id: str) -> TradeRecord:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        trade = self._repository.get_trade(account_id=account_id, user_id=user_id, trade_id=trade_id)
        if trade is None:
            raise TradeNotFoundError("trade not found")
        return trade

    def list_trades(self, *, user_id: str, account_id: str) -> list[TradeRecord]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_trades(account_id=account_id, user_id=user_id)

    def deposit(self, *, user_id: str, account_id: str, amount: float) -> CashFlow:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        if amount <= 0:
            raise ValueError("amount must be positive")

        flow = CashFlow.create(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            flow_type="deposit",
        )
        self._repository.save_cash_flow(flow)
        return flow

    def withdraw(self, *, user_id: str, account_id: str, amount: float) -> CashFlow:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        if amount <= 0:
            raise ValueError("amount must be positive")

        current_balance = self.cash_balance(user_id=user_id, account_id=account_id)
        if current_balance < amount:
            raise InsufficientFundsError("insufficient funds")

        flow = CashFlow.create(
            user_id=user_id,
            account_id=account_id,
            amount=-amount,
            flow_type="withdraw",
        )
        self._repository.save_cash_flow(flow)
        return flow

    def list_cash_flows(self, *, user_id: str, account_id: str) -> list[CashFlow]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        return self._repository.list_cash_flows(account_id=account_id, user_id=user_id)

    def cash_balance(self, *, user_id: str, account_id: str) -> float:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        flows = self._repository.list_cash_flows(account_id=account_id, user_id=user_id)
        return sum(item.amount for item in flows)

    def position_summary(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        positions = self._repository.list_positions(account_id=account_id, user_id=user_id)
        total_market_value = sum(item.quantity * item.last_price for item in positions)
        total_cost = sum(item.quantity * item.avg_price for item in positions)
        unrealized_pnl = total_market_value - total_cost
        return {
            "positionCount": len(positions),
            "totalMarketValue": total_market_value,
            "unrealizedPnl": unrealized_pnl,
        }

    def trade_stats(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        trades = self._repository.list_trades(account_id=account_id, user_id=user_id)
        turnover = sum(item.quantity * item.price for item in trades)
        return {
            "tradeCount": len(trades),
            "turnover": turnover,
        }

    def account_risk_metrics(self, *, user_id: str, account_id: str) -> dict[str, Any]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        position_metrics = self.position_summary(user_id=user_id, account_id=account_id)
        cash_balance = self.cash_balance(user_id=user_id, account_id=account_id)
        orders = self._repository.list_orders(account_id=account_id, user_id=user_id)

        total_market_value = float(position_metrics["totalMarketValue"])
        unrealized_pnl = float(position_metrics["unrealizedPnl"])
        total_equity = cash_balance + total_market_value

        exposure_ratio = total_market_value / total_equity if total_equity > 0 else 0.0
        leverage = total_market_value / total_equity if total_equity > 0 else 0.0
        pending_order_count = sum(1 for item in orders if item.status == "pending")
        pending_order_ratio = pending_order_count / len(orders) if orders else 0.0

        pnl_penalty = 0.0
        if total_market_value > 0 and unrealized_pnl < 0:
            pnl_penalty = abs(unrealized_pnl) / total_market_value

        risk_score = round(min(100.0, exposure_ratio * 60 + pnl_penalty * 30 + pending_order_ratio * 10), 2)

        return {
            "accountId": account_id,
            "riskScore": risk_score,
            "riskLevel": self._to_risk_level(score=risk_score),
            "exposureRatio": round(exposure_ratio, 6),
            "leverage": round(leverage, 6),
            "unrealizedPnl": unrealized_pnl,
            "pendingOrderCount": pending_order_count,
            "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        }

    def account_equity_curve(self, *, user_id: str, account_id: str) -> list[dict[str, Any]]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        flows = sorted(
            self._repository.list_cash_flows(account_id=account_id, user_id=user_id),
            key=lambda item: item.created_at,
        )

        positions = self._repository.list_positions(account_id=account_id, user_id=user_id)
        market_value = sum(item.quantity * item.last_price for item in positions)

        if not flows:
            now = datetime.now(timezone.utc).isoformat()
            return [
                {
                    "timestamp": now,
                    "cashBalance": 0.0,
                    "marketValue": market_value,
                    "equity": market_value,
                }
            ]

        curve: list[dict[str, Any]] = []
        cash_balance = 0.0
        for flow in flows:
            cash_balance += flow.amount
            curve.append(
                {
                    "timestamp": flow.created_at.isoformat(),
                    "cashBalance": round(cash_balance, 6),
                    "marketValue": round(market_value, 6),
                    "equity": round(cash_balance + market_value, 6),
                }
            )

        return curve

    def account_position_analysis(self, *, user_id: str, account_id: str) -> list[dict[str, Any]]:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        positions = self._repository.list_positions(account_id=account_id, user_id=user_id)

        total_market_value = sum(item.quantity * item.last_price for item in positions)
        items: list[dict[str, Any]] = []
        for position in positions:
            market_value = position.quantity * position.last_price
            cost_value = position.quantity * position.avg_price
            unrealized_pnl = market_value - cost_value
            weight = market_value / total_market_value if total_market_value > 0 else 0.0
            pnl_ratio = unrealized_pnl / cost_value if cost_value > 0 else 0.0

            items.append(
                {
                    "symbol": position.symbol,
                    "quantity": position.quantity,
                    "avgPrice": position.avg_price,
                    "lastPrice": position.last_price,
                    "marketValue": round(market_value, 6),
                    "costValue": round(cost_value, 6),
                    "unrealizedPnl": round(unrealized_pnl, 6),
                    "unrealizedPnlRatio": round(pnl_ratio, 6),
                    "weight": round(weight, 6),
                }
            )

        items.sort(key=lambda item: item["marketValue"], reverse=True)
        return items

    def user_account_aggregate(self, *, user_id: str) -> dict[str, Any]:
        accounts = self.list_accounts(user_id=user_id)

        total_cash_balance = 0.0
        total_market_value = 0.0
        total_unrealized_pnl = 0.0
        total_trade_count = 0
        total_turnover = 0.0
        total_pending_orders = 0

        for account in accounts:
            cash_balance = self.cash_balance(user_id=user_id, account_id=account.id)
            position_metrics = self.position_summary(user_id=user_id, account_id=account.id)
            trade_metrics = self.trade_stats(user_id=user_id, account_id=account.id)
            orders = self._repository.list_orders(account_id=account.id, user_id=user_id)

            total_cash_balance += cash_balance
            total_market_value += float(position_metrics["totalMarketValue"])
            total_unrealized_pnl += float(position_metrics["unrealizedPnl"])
            total_trade_count += int(trade_metrics["tradeCount"])
            total_turnover += float(trade_metrics["turnover"])
            total_pending_orders += sum(1 for item in orders if item.status == "pending")

        total_equity = total_cash_balance + total_market_value

        return {
            "userId": user_id,
            "accountCount": len(accounts),
            "totalCashBalance": round(total_cash_balance, 6),
            "totalMarketValue": round(total_market_value, 6),
            "totalUnrealizedPnl": round(total_unrealized_pnl, 6),
            "totalEquity": round(total_equity, 6),
            "totalTradeCount": total_trade_count,
            "totalTurnover": round(total_turnover, 6),
            "pendingOrderCount": total_pending_orders,
        }

    def list_pending_orders(
        self,
        *,
        user_id: str,
        is_admin: bool,
        admin_decision_source: str = "unknown",
        account_id: str | None = None,
    ) -> list[TradeOrder]:
        if not is_admin:
            raise TradingAdminRequiredError("admin role required")
        del admin_decision_source
        if account_id is not None:
            return self._repository.list_orders_by_status(status="pending", account_id=account_id)
        return self._repository.list_orders_by_status(status="pending")

    def refresh_market_prices(
        self,
        *,
        user_id: str,
        is_admin: bool,
        admin_decision_source: str = "unknown",
        price_updates: dict[str, float],
        idempotency_key: str | None = None,
        confirmation_token: str | None = None,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        if not price_updates:
            raise ValueError("price updates must not be empty")

        if self._governance_checker is not None:
            role = "admin" if is_admin else "user"
            level = 10 if is_admin else 1
            try:
                self._governance_checker(
                    actor_id=user_id,
                    role=role,
                    level=level,
                    action="trading.refresh_prices",
                    target="trading",
                    confirmation_token=confirmation_token,
                    context={
                        "actor": user_id,
                        "token": confirmation_token or "",
                        "adminDecisionSource": admin_decision_source,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                raise TradingAdminRequiredError(str(exc)) from exc
        elif not is_admin:
            raise TradingAdminRequiredError("admin role required")

        fingerprint = self._refresh_fingerprint(price_updates=price_updates, account_id=account_id)
        if idempotency_key:
            existed = self._refresh_records.get((user_id, idempotency_key))
            if existed is not None:
                stored_fingerprint, stored_result = existed
                if stored_fingerprint != fingerprint:
                    raise PriceRefreshConflictError("idempotency key already exists")
                replay = dict(stored_result)
                replay["idempotent"] = True
                return replay

        updated = self._repository.refresh_position_prices(
            price_updates=price_updates,
            account_id=account_id,
            user_id=None,
        )
        result = {
            "updatedPositions": updated,
            "symbols": sorted(price_updates.keys()),
            "idempotent": False,
        }

        if idempotency_key:
            self._refresh_records[(user_id, idempotency_key)] = (fingerprint, dict(result))

        return result

    def account_overview(self, *, user_id: str, account_id: str) -> dict:
        self._assert_account_owner(user_id=user_id, account_id=account_id)
        order_list = self._repository.list_orders(account_id=account_id, user_id=user_id)
        position_metrics = self.position_summary(user_id=user_id, account_id=account_id)
        trade_metrics = self.trade_stats(user_id=user_id, account_id=account_id)
        cash_balance = self.cash_balance(user_id=user_id, account_id=account_id)

        status_counts = {
            "pendingOrderCount": 0,
            "filledOrderCount": 0,
            "cancelledOrderCount": 0,
            "failedOrderCount": 0,
        }
        for item in order_list:
            key = f"{item.status}OrderCount"
            if key in status_counts:
                status_counts[key] += 1

        return {
            **position_metrics,
            **trade_metrics,
            "orderCount": len(order_list),
            **status_counts,
            "cashBalance": cash_balance,
        }
