"""user-preferences FastAPI 路由。

该模块提供 `APIRouter`，方便挂载到任意 FastAPI app。
"""

from __future__ import annotations

from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException

from platform_core.response import success_response
from user_preferences.domain import (
    AdvancedPreferencesPermissionError,
    Preferences,
    PreferencesValidationError,
    apply_patch,
    filter_for_user,
    migrate_preferences,
)
from user_preferences.store import PreferencesStore


def create_router(
    *,
    store: PreferencesStore,
    get_current_user: Any,
) -> APIRouter:
    router = APIRouter()

    @router.get("/users/me/preferences")
    def get_preferences(current_user=Depends(get_current_user)):
        prefs = store.get_or_create(current_user.id)
        filtered = filter_for_user(prefs, user_level=getattr(current_user, "level", 1))
        return success_response(data=filtered.model_dump(by_alias=True, exclude_none=True))

    @router.patch("/users/me/preferences")
    def patch_preferences(body: Mapping[str, Any], current_user=Depends(get_current_user)):
        prefs = store.get_or_create(current_user.id)
        try:
            updated = apply_patch(prefs, body, user_level=getattr(current_user, "level", 1))
        except AdvancedPreferencesPermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        except PreferencesValidationError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        store.set(current_user.id, updated)
        filtered = filter_for_user(updated, user_level=getattr(current_user, "level", 1))
        return success_response(data=filtered.model_dump(by_alias=True, exclude_none=True))

    @router.post("/users/me/preferences/reset")
    def reset_preferences(current_user=Depends(get_current_user)):
        prefs = store.reset(current_user.id)
        filtered = filter_for_user(prefs, user_level=getattr(current_user, "level", 1))
        return success_response(data=filtered.model_dump(by_alias=True, exclude_none=True))

    @router.get("/users/me/preferences/export")
    def export_preferences(current_user=Depends(get_current_user)):
        prefs = store.get_or_create(current_user.id)
        filtered = filter_for_user(prefs, user_level=getattr(current_user, "level", 1))
        return success_response(data=filtered.model_dump(by_alias=True, exclude_none=True))

    @router.post("/users/me/preferences/import")
    def import_preferences(body: Mapping[str, Any], current_user=Depends(get_current_user)):
        try:
            incoming = migrate_preferences(body)
        except Exception as e:  # pragma: no cover
            raise HTTPException(status_code=422, detail=str(e)) from e
        # 权限：低等级用户导入时不能包含 advanced
        if incoming.advanced is not None and getattr(current_user, "level", 1) < 2:
            raise HTTPException(status_code=403, detail="advanced requires elevated user level")
        store.set(current_user.id, incoming)
        filtered = filter_for_user(incoming, user_level=getattr(current_user, "level", 1))
        return success_response(data=filtered.model_dump(by_alias=True, exclude_none=True))

    return router
