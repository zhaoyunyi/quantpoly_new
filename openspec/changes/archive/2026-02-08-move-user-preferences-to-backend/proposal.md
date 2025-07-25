# 提案：move-user-preferences-to-backend

## Why（为什么要做）

旧项目中用户偏好设置（preferences）由 better-auth 用户表承载，但前端仍参与了偏好结构与默认值的演进，且后端存在“浅合并 / 无权限校验 / 无 reset/export/import”等缺口。

迁移目标要求“用户系统相关内容全部聚合到后端”，因此偏好设置必须成为后端能力：

- 默认值、版本迁移、校验规则、权限（例如 `advanced` 字段仅高等级用户）
- API 读写、导入导出、重置

## What Changes（做什么）

- 新增 `user-preferences` capability spec：
  - 读取/更新（支持深度合并策略）
  - `advanced` 权限控制
  - reset/export/import
  - 版本迁移（preferences schema versioning）

## Impact（影响）

- 前端仅展示与编辑偏好，不再决定默认值/校验规则
- 为风控/回测等模块提供一致的用户配置来源

