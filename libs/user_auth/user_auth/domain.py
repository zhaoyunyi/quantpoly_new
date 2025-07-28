"""用户认证领域模型。

聚合根：User
值对象：Credential
"""
import uuid
from dataclasses import dataclass, field

import bcrypt


class PasswordTooWeakError(ValueError):
    """密码强度不足。"""
    pass


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
        raise PasswordTooWeakError(
            "Password does not meet security requirements."
        )


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
        return bcrypt.checkpw(
            raw_password.encode(),
            self.hashed_password.encode(),
        )


@dataclass
class User:
    """用户聚合根。"""

    id: str
    email: str
    credential: Credential
    is_active: bool = True
    email_verified: bool = False

    @classmethod
    def register(cls, email: str, password: str) -> "User":
        _validate_password_strength(password)
        credential = Credential.create(password)
        return cls(
            id=str(uuid.uuid4()),
            email=email,
            credential=credential,
        )

    def authenticate(self, password: str) -> bool:
        return self.credential.verify(password)

    def verify_email(self) -> None:
        self.email_verified = True
