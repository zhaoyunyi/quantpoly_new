"""用户仓储（内存实现）。"""

from __future__ import annotations

from user_auth.domain import User


class UserRepository:
    """内存用户存储（生产环境应替换为数据库实现）。"""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}

    def save(self, user: User) -> None:
        existing = self._users.get(user.id)
        if existing is not None and existing.email != user.email:
            stale_owner = self._email_index.get(existing.email)
            if stale_owner == user.id:
                self._email_index.pop(existing.email, None)
        self._users[user.id] = user
        self._email_index[user.email] = user.id

    def get_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        uid = self._email_index.get(email)
        if uid is None:
            return None
        return self._users.get(uid)

    def email_exists(self, email: str) -> bool:
        return email in self._email_index

    def list_users(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        users = list(self._users.values())
        if status is not None:
            active = status == "active"
            users = [item for item in users if item.is_active is active]

        total = len(users)
        start = max(0, page - 1) * page_size
        end = start + page_size
        return {
            "items": users[start:end],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }

    def update_user_level(self, *, user_id: str, level: int) -> User | None:
        user = self._users.get(user_id)
        if user is None:
            return None
        user.set_level(level)
        self.save(user)
        return user

    def update_user_status(self, *, user_id: str, is_active: bool) -> User | None:
        user = self._users.get(user_id)
        if user is None:
            return None
        if is_active:
            user.enable()
        else:
            user.disable()
        self.save(user)
        return user

    def delete(self, user_id: str) -> bool:
        user = self._users.pop(user_id, None)
        if user is None:
            return False

        owner = self._email_index.get(user.email)
        if owner == user_id:
            self._email_index.pop(user.email, None)
        return True
