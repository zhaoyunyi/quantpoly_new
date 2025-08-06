"""用户认证领域模型。

聚合根：User
值对象：Credential
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import bcrypt


class PasswordTooWeakError(ValueError):
    """密码强度不足。"""


_MIN_PASSWORD_LENGTH = 8


def _validate_password_strength(password: str) -> None:
    """校验密码强度，不泄漏具体策略细节。"""
    is_weak = (
        len(password) < _MIN_PASSWORD_LENGTH
        or not any(c.isdigit() for c in password)
        or not any(c.isupper() for c in password)
        or not any(c.islower() for c in password)
    )
    if is_weak:
        raise PasswordTooWeakError("Password does not meet security requirements.")


@dataclass(frozen=True)
class Credential:
    """密码凭证值对象。"""

    hashed_password: str

    @classmethod
    def create(cls, raw_password: str) -> "Credential":
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(raw_password.encode(), salt).decode()
        return cls(hashed_password=hashed)

    def verify(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode(), self.hashed_password.encode())


@dataclass
class User:
    """用户聚合根。"""

    id: str
    email: str
    credential: Credential
    is_active: bool = True
    email_verified: bool = False
    role: str = "user"
    level: int = 1
    display_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def register(cls, email: str, password: str) -> "User":
        _validate_password_strength(password)
        credential = Credential.create(password)
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            email=email,
            credential=credential,
            created_at=now,
            updated_at=now,
        )

    def authenticate(self, password: str) -> bool:
        return self.credential.verify(password)

    def verify_email(self) -> None:
        self.email_verified = True
        self.updated_at = datetime.now(timezone.utc)

    def update_profile(
        self,
        *,
        email: str | None = None,
        display_name: str | None = None,
    ) -> None:
        if email is not None:
            self.email = email
        if display_name is not None:
            self.display_name = display_name
        self.updated_at = datetime.now(timezone.utc)

    def set_level(self, level: int) -> None:
        if level < 1 or level > 2:
            raise ValueError("level must be between 1 and 2")
        self.level = level
        self.updated_at = datetime.now(timezone.utc)

    def set_role(self, role: str) -> None:
        if role not in {"user", "admin"}:
            raise ValueError("role must be user or admin")
        self.role = role
        self.updated_at = datetime.now(timezone.utc)

    def disable(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def enable(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def change_password(self, *, current_password: str, new_password: str) -> None:
        if not self.authenticate(current_password):
            raise ValueError("current password mismatch")
        if current_password == new_password:
            raise ValueError("new password cannot equal current password")

        _validate_password_strength(new_password)
        self.credential = Credential.create(new_password)
        self.updated_at = datetime.now(timezone.utc)
