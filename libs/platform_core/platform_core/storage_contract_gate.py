"""存储契约门禁评估逻辑。"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_DEFAULT_MODULE_NAMES = [
    "user_auth",
    "user_preferences",
    "strategy_management",
    "backtest_runner",
    "job_orchestration",
    "trading_account",
    "risk_control",
    "signal_execution",
]

_DEFAULT_FORBIDDEN_TOKENS = ["sqlite", "SQLite"]


@dataclass
class StorageContractGateInput:
    module_names: list[str]
    forbidden_tokens: list[str]
    modules: list[dict[str, Any]] | None = None


def parse_storage_contract_input(payload: dict[str, Any]) -> StorageContractGateInput:
    modules_payload = payload.get("modules")
    if modules_payload is not None:
        if not isinstance(modules_payload, list):
            raise ValueError("modules must be a list")
        for item in modules_payload:
            if not isinstance(item, dict):
                raise ValueError("modules item must be an object")
            name = item.get("name")
            exports = item.get("exports")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("modules item name must be a non-empty string")
            if not isinstance(exports, list):
                raise ValueError("modules item exports must be a list")
            if not all(isinstance(export, str) for export in exports):
                raise ValueError("modules item exports must contain only strings")

    module_names_value = payload.get("moduleNames")
    if module_names_value is None:
        module_names = list(_DEFAULT_MODULE_NAMES)
    else:
        if not isinstance(module_names_value, list) or not all(isinstance(item, str) for item in module_names_value):
            raise ValueError("moduleNames must be a list of strings")
        module_names = [item for item in module_names_value if item.strip()]

    forbidden_tokens_value = payload.get("forbiddenTokens")
    if forbidden_tokens_value is None:
        forbidden_tokens = list(_DEFAULT_FORBIDDEN_TOKENS)
    else:
        if not isinstance(forbidden_tokens_value, list) or not all(
            isinstance(item, str) for item in forbidden_tokens_value
        ):
            raise ValueError("forbiddenTokens must be a list of strings")
        forbidden_tokens = [item for item in forbidden_tokens_value if item]

    if not forbidden_tokens:
        raise ValueError("forbiddenTokens must not be empty")

    return StorageContractGateInput(
        module_names=module_names,
        forbidden_tokens=forbidden_tokens,
        modules=modules_payload,
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _module_init_file(module_name: str) -> Path:
    return _repo_root() / "libs" / module_name / module_name / "__init__.py"


def _read_exports_from_init(module_name: str) -> list[str]:
    path = _module_init_file(module_name)
    if not path.exists():
        raise ModuleNotFoundError(f"module init file not found: {path}")

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "__all__":
            continue

        if not isinstance(node.value, (ast.List, ast.Tuple)):
            return []

        exports: list[str] = []
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                exports.append(element.value)
        return exports

    return []


def _collect_exports_from_filesystem(module_names: list[str]) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for module_name in module_names:
        exports = _read_exports_from_init(module_name)
        modules.append({"name": module_name, "exports": exports})
    return modules


def _match_forbidden_token(*, export: str, forbidden_tokens: list[str]) -> str | None:
    export_lower = export.lower()
    for token in forbidden_tokens:
        if token.lower() in export_lower:
            return token
    return None


def evaluate_storage_contract_gate(payload: dict[str, Any]) -> dict[str, Any]:
    gate_input = parse_storage_contract_input(payload)

    if gate_input.modules is not None:
        checked_modules = gate_input.modules
        source = "input"
    else:
        checked_modules = _collect_exports_from_filesystem(gate_input.module_names)
        source = "filesystem"

    violations: list[dict[str, Any]] = []
    modules_summary: list[dict[str, Any]] = []
    total_exports = 0

    for module in checked_modules:
        module_name = str(module.get("name") or "unknown")
        exports = module.get("exports") or []
        export_names = [str(item) for item in exports]

        module_violations = 0
        for export in export_names:
            token = _match_forbidden_token(export=export, forbidden_tokens=gate_input.forbidden_tokens)
            if token is None:
                continue
            module_violations += 1
            violations.append(
                {
                    "module": module_name,
                    "export": export,
                    "token": token,
                    "code": "FORBIDDEN_EXPORT_TOKEN",
                }
            )

        total_exports += len(export_names)
        modules_summary.append(
            {
                "name": module_name,
                "exportCount": len(export_names),
                "violations": module_violations,
            }
        )

    return {
        "allowed": len(violations) == 0,
        "source": source,
        "forbiddenTokens": gate_input.forbidden_tokens,
        "summary": {
            "checkedModules": len(checked_modules),
            "checkedExports": total_exports,
            "violations": len(violations),
        },
        "modules": modules_summary,
        "violations": violations,
    }
