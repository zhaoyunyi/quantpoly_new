"""用户仓储（内存实现）。"""
from user_auth.domain import User


class UserRepository:
    """内存用户存储（生产环境应替换为数据库实现）。"""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}

    def save(self, user: User) -> None:
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
