"""资源所有权（ownership）校验测试。

覆盖的 BDD 场景（来自 change: update-backend-user-ownership）：
- 列表接口按当前用户过滤
- 读取单个资源拒绝越权（403）
- 更新/删除资源拒绝越权（403）
- Repository/Service 层必须显式接收 user_id
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def _build_app(repo) -> FastAPI:
    app = FastAPI()

    def get_current_user_id() -> str:
        return "u1"

    @app.get("/resources")
    def list_resources(current_user_id: str = Depends(get_current_user_id)):
        items = repo.list(user_id=current_user_id)
        return {"success": True, "data": {"items": items}}

    @app.get("/resources/{resource_id}")
    def get_resource(resource_id: str, current_user_id: str = Depends(get_current_user_id)):
        from platform_core.fastapi.ownership import raise_ownership_forbidden
        from platform_core.ownership import OwnershipViolationError

        try:
            resource = repo.get_by_id(resource_id, user_id=current_user_id)
            return {"success": True, "data": resource}
        except OwnershipViolationError:
            raise_ownership_forbidden()

    @app.delete("/resources/{resource_id}")
    def delete_resource(resource_id: str, current_user_id: str = Depends(get_current_user_id)):
        from platform_core.fastapi.ownership import raise_ownership_forbidden
        from platform_core.ownership import OwnershipViolationError

        try:
            repo.delete(resource_id, user_id=current_user_id)
            return {"success": True}
        except OwnershipViolationError:
            raise_ownership_forbidden()

    @app.patch("/resources/{resource_id}")
    def patch_resource(
        resource_id: str,
        payload: dict,
        current_user_id: str = Depends(get_current_user_id),
    ):
        from platform_core.fastapi.ownership import raise_ownership_forbidden
        from platform_core.ownership import OwnershipViolationError

        try:
            resource = repo.update(resource_id, user_id=current_user_id, data=payload)
            return {"success": True, "data": resource}
        except OwnershipViolationError:
            raise_ownership_forbidden()

    return app


class TestOwnedResourceRepository:
    def test_list_filters_by_user_id(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u1", data={"name": "mine"})
        repo.save(id="r2", user_id="u2", data={"name": "theirs"})

        items = repo.list(user_id="u1")
        assert [i["id"] for i in items] == ["r1"]

    def test_get_by_id_raises_when_not_owner(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository, OwnershipViolationError

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u2", data={"name": "theirs"})

        try:
            repo.get_by_id("r1", user_id="u1")
            assert False, "should raise"
        except OwnershipViolationError:
            assert True

    def test_update_raises_when_not_owner(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository, OwnershipViolationError

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u2", data={"name": "theirs"})

        try:
            repo.update("r1", user_id="u1", data={"name": "hack"})
            assert False, "should raise"
        except OwnershipViolationError:
            assert True


class TestFastAPIOwnership:
    def test_list_only_returns_current_user_resources(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u1", data={"name": "mine"})
        repo.save(id="r2", user_id="u2", data={"name": "theirs"})
        app = _build_app(repo)

        client = TestClient(app)
        resp = client.get("/resources")
        assert resp.status_code == 200
        data = resp.json()
        assert [i["id"] for i in data["data"]["items"]] == ["r1"]

    def test_get_returns_403_when_not_owner(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u2", data={"name": "theirs"})
        app = _build_app(repo)

        client = TestClient(app)
        resp = client.get("/resources/r1")
        assert resp.status_code == 403

    def test_delete_returns_403_when_not_owner(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u2", data={"name": "theirs"})
        app = _build_app(repo)

        client = TestClient(app)
        resp = client.delete("/resources/r1")
        assert resp.status_code == 403

    def test_patch_returns_403_when_not_owner(self):
        from platform_core.ownership import InMemoryOwnedResourceRepository

        repo = InMemoryOwnedResourceRepository()
        repo.save(id="r1", user_id="u2", data={"name": "theirs"})
        app = _build_app(repo)

        client = TestClient(app)
        resp = client.patch("/resources/r1", json={"name": "hack"})
        assert resp.status_code == 403
