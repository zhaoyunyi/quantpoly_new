"""risk_control Postgres 持久化仓储。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from risk_control.domain import RiskAlert, RiskAssessmentSnapshot, RiskRule


class PostgresRiskRepository:
    def __init__(self, *, engine: Any) -> None:
        self._engine = engine
        self._init_schema()

    @staticmethod
    def _execute(conn, sql: str, params: tuple | list | None = None):
        normalized_sql = sql.replace("?", "%s")
        if params is None:
            return conn.exec_driver_sql(normalized_sql)
        return conn.exec_driver_sql(normalized_sql, tuple(params))



    def _init_schema(self) -> None:
        with self._engine.begin() as conn:
            self._execute(conn, 
                """
                CREATE TABLE IF NOT EXISTS risk_control_rule (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    strategy_id TEXT,
                    rule_name TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    is_active INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._execute(conn, 
                """
                CREATE TABLE IF NOT EXISTS risk_control_alert (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    acknowledged_by TEXT,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    notification_status TEXT,
                    notified_at TEXT,
                    notified_by TEXT
                )
                """
            )
            self._execute(conn, 
                """
                CREATE TABLE IF NOT EXISTS risk_control_assessment (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    strategy_id TEXT,
                    risk_score REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    triggered_rule_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _dt(value: str | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value)

    @staticmethod
    def _rule_from_row(row) -> RiskRule:
        return RiskRule(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            strategy_id=row[3],
            rule_name=row[4],
            threshold=float(row[5]),
            is_active=bool(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8]),
        )

    @classmethod
    def _alert_from_row(cls, row) -> RiskAlert:
        return RiskAlert(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            rule_name=row[3],
            severity=row[4],
            message=row[5],
            status=row[6],
            created_at=datetime.fromisoformat(row[7]),
            acknowledged_at=cls._dt(row[8]),
            acknowledged_by=row[9],
            resolved_at=cls._dt(row[10]),
            resolved_by=row[11],
            notification_status=row[12],
            notified_at=cls._dt(row[13]),
            notified_by=row[14],
        )

    @staticmethod
    def _assessment_from_row(row) -> RiskAssessmentSnapshot:
        return RiskAssessmentSnapshot(
            id=row[0],
            user_id=row[1],
            account_id=row[2],
            strategy_id=row[3],
            risk_score=float(row[4]),
            risk_level=row[5],
            triggered_rule_ids=list(json.loads(row[6] or "[]")),
            created_at=datetime.fromisoformat(row[7]),
        )

    def save_rule(self, rule: RiskRule) -> None:
        with self._engine.begin() as conn:
            self._execute(conn, 
                """
                INSERT INTO risk_control_rule
                    (id, user_id, account_id, strategy_id, rule_name, threshold, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_id = excluded.account_id,
                    strategy_id = excluded.strategy_id,
                    rule_name = excluded.rule_name,
                    threshold = excluded.threshold,
                    is_active = excluded.is_active,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    rule.id,
                    rule.user_id,
                    rule.account_id,
                    rule.strategy_id,
                    rule.rule_name,
                    rule.threshold,
                    1 if rule.is_active else 0,
                    rule.created_at.isoformat(),
                    rule.updated_at.isoformat(),
                ),
            )

    def get_rule(self, *, rule_id: str, user_id: str) -> RiskRule | None:
        with self._engine.begin() as conn:
            row = self._execute(conn, 
                """
                SELECT id, user_id, account_id, strategy_id, rule_name, threshold, is_active, created_at, updated_at
                FROM risk_control_rule
                WHERE id = ? AND user_id = ?
                """,
                (rule_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return self._rule_from_row(row)

    def delete_rule(self, *, rule_id: str, user_id: str) -> bool:
        with self._engine.begin() as conn:
            cursor = self._execute(conn, 
                "DELETE FROM risk_control_rule WHERE id = ? AND user_id = ?",
                (rule_id, user_id),
            )
        return cursor.rowcount > 0

    def list_rules(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        strategy_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[RiskRule]:
        clauses = ["user_id = ?"]
        params: list[object] = [user_id]

        if account_id is not None:
            clauses.append("account_id = ?")
            params.append(account_id)
        if strategy_id is not None:
            clauses.append("strategy_id = ?")
            params.append(strategy_id)
        if is_active is not None:
            clauses.append("is_active = ?")
            params.append(1 if is_active else 0)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT id, user_id, account_id, strategy_id, rule_name, threshold, is_active, created_at, updated_at "
            "FROM risk_control_rule "
            f"WHERE {where_sql} "
            "ORDER BY created_at ASC"
        )
        with self._engine.begin() as conn:
            rows = self._execute(conn, sql, params).fetchall()
        return [self._rule_from_row(item) for item in rows]

    def list_applicable_rules(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> list[RiskRule]:
        rules = self.list_rules(user_id=user_id, account_id=account_id, is_active=True)
        if strategy_id is None:
            return [item for item in rules if item.strategy_id is None]

        return [
            item
            for item in rules
            if item.strategy_id is None or item.strategy_id == strategy_id
        ]

    def save_alert(self, alert: RiskAlert) -> None:
        with self._engine.begin() as conn:
            self._execute(conn, 
                """
                INSERT INTO risk_control_alert
                    (
                        id, user_id, account_id, rule_name, severity, message, status,
                        created_at, acknowledged_at, acknowledged_by,
                        resolved_at, resolved_by,
                        notification_status, notified_at, notified_by
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_id = excluded.account_id,
                    rule_name = excluded.rule_name,
                    severity = excluded.severity,
                    message = excluded.message,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    acknowledged_at = excluded.acknowledged_at,
                    acknowledged_by = excluded.acknowledged_by,
                    resolved_at = excluded.resolved_at,
                    resolved_by = excluded.resolved_by,
                    notification_status = excluded.notification_status,
                    notified_at = excluded.notified_at,
                    notified_by = excluded.notified_by
                """,
                (
                    alert.id,
                    alert.user_id,
                    alert.account_id,
                    alert.rule_name,
                    alert.severity,
                    alert.message,
                    alert.status,
                    alert.created_at.isoformat(),
                    alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    alert.acknowledged_by,
                    alert.resolved_at.isoformat() if alert.resolved_at else None,
                    alert.resolved_by,
                    alert.notification_status,
                    alert.notified_at.isoformat() if alert.notified_at else None,
                    alert.notified_by,
                ),
            )

    def get_alert(self, *, alert_id: str, user_id: str) -> RiskAlert | None:
        with self._engine.begin() as conn:
            row = self._execute(conn, 
                """
                SELECT
                    id, user_id, account_id, rule_name, severity, message, status,
                    created_at, acknowledged_at, acknowledged_by,
                    resolved_at, resolved_by,
                    notification_status, notified_at, notified_by
                FROM risk_control_alert
                WHERE id = ? AND user_id = ?
                """,
                (alert_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return self._alert_from_row(row)

    def list_alerts(
        self,
        *,
        user_id: str,
        account_id: str | None = None,
        status: str | None = None,
    ) -> list[RiskAlert]:
        clauses = ["user_id = ?"]
        params: list[object] = [user_id]

        if account_id is not None:
            clauses.append("account_id = ?")
            params.append(account_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT "
            "id, user_id, account_id, rule_name, severity, message, status, "
            "created_at, acknowledged_at, acknowledged_by, "
            "resolved_at, resolved_by, notification_status, notified_at, notified_by "
            "FROM risk_control_alert "
            f"WHERE {where_sql} "
            "ORDER BY created_at ASC"
        )

        with self._engine.begin() as conn:
            rows = self._execute(conn, sql, params).fetchall()
        return [self._alert_from_row(item) for item in rows]

    def list_alerts_by_ids(self, *, alert_ids: list[str]) -> list[RiskAlert]:
        if not alert_ids:
            return []

        placeholders = ",".join("?" for _ in alert_ids)
        sql = (
            "SELECT "
            "id, user_id, account_id, rule_name, severity, message, status, "
            "created_at, acknowledged_at, acknowledged_by, "
            "resolved_at, resolved_by, notification_status, notified_at, notified_by "
            "FROM risk_control_alert "
            f"WHERE id IN ({placeholders})"
        )
        with self._engine.begin() as conn:
            rows = self._execute(conn, sql, alert_ids).fetchall()

        by_id = {item[0]: self._alert_from_row(item) for item in rows}
        return [by_id[item_id] for item_id in alert_ids if item_id in by_id]

    def delete_resolved_alerts_older_than(self, *, user_id: str, cutoff: datetime) -> int:
        with self._engine.begin() as conn:
            cursor = self._execute(conn, 
                """
                DELETE FROM risk_control_alert
                WHERE user_id = ?
                  AND status = 'resolved'
                  AND resolved_at IS NOT NULL
                  AND resolved_at < ?
                """,
                (user_id, cutoff.isoformat()),
            )
        return cursor.rowcount

    def save_assessment(self, snapshot: RiskAssessmentSnapshot) -> None:
        with self._engine.begin() as conn:
            self._execute(conn, 
                """
                INSERT INTO risk_control_assessment
                    (id, user_id, account_id, strategy_id, risk_score, risk_level, triggered_rule_ids, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    account_id = excluded.account_id,
                    strategy_id = excluded.strategy_id,
                    risk_score = excluded.risk_score,
                    risk_level = excluded.risk_level,
                    triggered_rule_ids = excluded.triggered_rule_ids,
                    created_at = excluded.created_at
                """,
                (
                    snapshot.id,
                    snapshot.user_id,
                    snapshot.account_id,
                    snapshot.strategy_id,
                    snapshot.risk_score,
                    snapshot.risk_level,
                    json.dumps(snapshot.triggered_rule_ids, ensure_ascii=False),
                    snapshot.created_at.isoformat(),
                ),
            )

    def list_assessments(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> list[RiskAssessmentSnapshot]:
        clauses = ["user_id = ?", "account_id = ?"]
        params: list[object] = [user_id, account_id]

        if strategy_id is None:
            clauses.append("strategy_id IS NULL")
        else:
            clauses.append("strategy_id = ?")
            params.append(strategy_id)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT id, user_id, account_id, strategy_id, risk_score, risk_level, triggered_rule_ids, created_at "
            "FROM risk_control_assessment "
            f"WHERE {where_sql} "
            "ORDER BY created_at ASC"
        )
        with self._engine.begin() as conn:
            rows = self._execute(conn, sql, params).fetchall()
        return [self._assessment_from_row(item) for item in rows]

    def get_latest_assessment(
        self,
        *,
        user_id: str,
        account_id: str,
        strategy_id: str | None = None,
    ) -> RiskAssessmentSnapshot | None:
        matched = self.list_assessments(
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
        )
        if not matched:
            return None
        return max(matched, key=lambda item: item.created_at)

    def get_latest_strategy_assessment(
        self,
        *,
        user_id: str,
        account_id: str,
    ) -> RiskAssessmentSnapshot | None:
        with self._engine.begin() as conn:
            row = self._execute(conn, 
                """
                SELECT id, user_id, account_id, strategy_id, risk_score, risk_level, triggered_rule_ids, created_at
                FROM risk_control_assessment
                WHERE user_id = ? AND account_id = ? AND strategy_id IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, account_id),
            ).fetchone()
        if row is None:
            return None
        return self._assessment_from_row(row)
