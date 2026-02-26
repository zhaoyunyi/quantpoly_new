# 本地密钥目录说明

此目录用于存放**仅本地使用**的部署密钥与令牌文件，不进入 Git 版本管理。

## 约束

- 所有真实密钥文件必须使用 `.local.env` 或 `.secret.env` 后缀。
- 本目录下真实密钥文件默认被 `.gitignore` 忽略。
- 不要在任何提交、PR、Issue、Skill 文档中写入真实密钥。

## 推荐文件命名

- `ops_tokens.local.env`
- `cloudflare.secret.env`
- `coolify.secret.env`

## 轮换建议

- 每次将密钥暴露在聊天、截图或日志后，立刻轮换。
- 轮换后同步更新本目录对应本地文件。
