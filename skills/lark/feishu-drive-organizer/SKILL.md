---
name: feishu-drive-organizer
description: 飞书云文档自动整理：OAuth 授权获取 user_access_token，递归扫描云盘/Wiki，生成 JSON + Markdown 索引
agent_created: true
---

# 飞书云文档整理 Skill

## 适用场景

- 需要系统化整理飞书个人云盘文件
- 需要导出文件树结构或 Markdown 索引
- 需要批量获取文档 URL 和元信息

## 前置条件

1. 飞书开放平台已创建应用，已知 `APP_ID` 和 `APP_SECRET`
2. 应用已开通权限：`drive:drive:readonly`、`wiki:wiki:readonly`、`contact:user.base:readonly`
3. 安全设置中已添加重定向 URL：`http://localhost:8080/callback`

## 核心认知

- **tenant_access_token（应用身份）**：无法访问用户个人云盘，只能访问应用自身创建的文件
- **user_access_token（用户身份）**：可访问个人云盘，必须通过 OAuth 授权流程获取
- 云盘 API 根目录 token 可通过 `drive/explorer/v2/root_folder/meta` 获取

## 使用方式

### 方式一：一键脚本（推荐）

保存脚本 `feishu_docs_auto.py`，双击运行：

```bash
python feishu_docs_auto.py
```

流程：
1. 自动打开浏览器到飞书 OAuth 授权页
2. 用户点击「允许授权」
3. 脚本自动接收回调、提取 code、交换 user_access_token
4. 递归扫描云盘 + Wiki
5. 输出 `feishu_docs_tree.json` 和 `feishu_docs_index.md`

### 方式二：环境变量模式

先手动获取 user_access_token（通过飞书后台或 OAuth），然后：

```bash
export FEISHU_USER_TOKEN=your_token
python feishu_organize_docs.py
```

## 关键 API

| 用途 | 端点 |
|------|------|
| 获取 app_access_token | `POST /auth/v3/app_access_token/internal` |
| OAuth 授权页 | `GET /authen/v1/index?app_id={id}&redirect_uri={uri}` |
| 交换 user_token | `POST /authen/v1/oidc/access_token` |
| 获取用户信息 | `GET /authen/v1/user_info` |
| 获取根目录 token | `GET /drive/explorer/v2/root_folder/meta` |
| 列出文件夹文件 | `GET /drive/v1/files?folder_token={token}` |
| 列出 Wiki 空间 | `GET /wiki/v2/spaces` |

## 输出文件

- `feishu_docs_tree.json`：完整文件树 JSON
- `feishu_docs_index.md`：Markdown 索引（带链接、图标、统计）
