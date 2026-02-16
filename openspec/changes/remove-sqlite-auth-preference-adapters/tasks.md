## 1. 用户认证与偏好 sqlite 代码移除

- [ ] 1.1 删除 `user_auth/*_sqlite.py` 与 sqlite 单测
- [ ] 1.2 删除 `user_preferences/store_sqlite.py` 与 sqlite 单测
- [ ] 1.3 更新 `__init__.py` 导出面与受影响测试

## 2. 验证

- [ ] 2.1 运行 user-auth / user-preferences / composition 测试集
- [ ] 2.2 运行全量 `pytest`
- [ ] 2.3 运行 `openspec validate remove-sqlite-auth-preference-adapters --strict`
