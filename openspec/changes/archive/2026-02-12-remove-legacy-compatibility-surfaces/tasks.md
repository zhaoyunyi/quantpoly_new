## 1. Implementation

- [x] 1.1 更新 job-orchestration spec：移除 legacyNames
- [x] 1.2 先写/改测试（Red）：断言 task-types 不再返回 legacyNames
- [x] 1.3 实现（Green）：task registry payload 去除 legacyNames
- [x] 1.4 运行 `openspec validate remove-legacy-compatibility-surfaces --strict`
- [x] 1.5 运行 `pytest`（至少覆盖 job_orchestration）
- [x] 1.6 使用 `git cnd` 提交，并归档 change
