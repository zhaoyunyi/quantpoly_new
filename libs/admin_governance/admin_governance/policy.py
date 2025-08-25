"""统一治理策略引擎。"""

from __future__ import annotations

from typing import Any

from platform_core.logging import mask_sensitive

from admin_governance.audit import InMemoryAuditLog
from admin_governance.domain import ActionPolicy, AuditRecord, PolicyResult
from admin_governance.token import InMemoryConfirmationTokenStore


class GovernanceAccessDeniedError(PermissionError):
    """治理策略拒绝访问。"""


class ConfirmationRequiredError(PermissionError):
    """高风险动作需要确认令牌。"""


def _mask_plain(value: str) -> str:
    if len(value) <= 4:
        return "***"
    return value[:4] + "***"


class GovernancePolicyEngine:
    def __init__(
        self,
        *,
        action_catalog: dict[str, ActionPolicy],
        token_store: InMemoryConfirmationTokenStore,
        audit_log: InMemoryAuditLog,
    ) -> None:
        self._action_catalog = action_catalog
        self._token_store = token_store
        self._audit_log = audit_log

    def _audit(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        result: str,
        context: dict[str, Any] | None,
    ) -> None:
        masked_context = {}
        sensitive_keys = {"token", "cookie", "password", "api_key", "secret", "authorization"}
        if context is not None:
            for key, value in context.items():
                if key.lower() in sensitive_keys:
                    masked_context[key] = _mask_plain(str(value))
                    continue

                if isinstance(value, str):
                    masked_context[key] = mask_sensitive(value)
                    continue

                if value is None or isinstance(value, (int, float, bool)):
                    masked_context[key] = value
                    continue

                masked_context[key] = mask_sensitive(str(value))

        self._audit_log.append(
            AuditRecord(
                actor=actor,
                action=action,
                target=target,
                result=result,
                context=masked_context,
            )
        )

    def authorize(
        self,
        *,
        actor_id: str,
        role: str,
        level: int,
        action: str,
        target: str,
        confirmation_token: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> PolicyResult:
        context_payload = dict(context or {})
        context_payload.setdefault(
            "adminDecisionSource",
            "role_level" if role == "admin" else "none",
        )

        policy = self._action_catalog.get(action)
        if policy is None:
            self._audit(actor=actor_id, action=action, target=target, result="denied", context=context_payload)
            raise GovernanceAccessDeniedError("action not in governance catalog")

        if role != policy.min_role or level < policy.min_level:
            self._audit(actor=actor_id, action=action, target=target, result="denied", context=context_payload)
            raise GovernanceAccessDeniedError("insufficient governance permission")

        if policy.requires_confirmation:
            if not confirmation_token:
                self._audit(actor=actor_id, action=action, target=target, result="denied", context=context_payload)
                raise ConfirmationRequiredError("confirmation token required")

            ok = self._token_store.consume(
                token=confirmation_token,
                actor_id=actor_id,
                action=action,
                target=target,
            )
            if not ok:
                self._audit(actor=actor_id, action=action, target=target, result="denied", context=context_payload)
                raise ConfirmationRequiredError("invalid or expired confirmation token")

        self._audit(actor=actor_id, action=action, target=target, result="allowed", context=context_payload)
        return PolicyResult(allowed=True, action=action, reason="authorized")
