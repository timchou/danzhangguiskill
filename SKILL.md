---
name: dan-erp-skill
description: Use this skill when a user needs to operate Dan ERP through merchant-scoped open APIs, especially for creating order drafts from chat content, understanding token-based authentication, or extending the skill with newly added ERP endpoints. This skill provides the required request conventions, auth rules, endpoint usage, and update pattern for future APIs.
metadata: {"openclaw":{"skillKey":"dan-erp-skill","homepage":"https://github.com/timchou/danzhangguiskill","primaryEnv":"DAN_ERP_TOKEN","requires":{"env":["DAN_ERP_TOKEN","DAN_ERP_BASE_URL"]}}}
---

# Dan ERP Skill

## Overview

这个 skill 用来让机器人通过单掌柜的开放接口帮商户办事。

当前已经支持：

- 用商户专属 token 调用开放接口
- 把聊天内容提交为订单草稿
- 通过内置脚本直接发起 API 请求

后续如果系统增加新的开放接口，也继续按这个 skill 的结构补充，不要另起一套说明。

## When To Use

遇到下面这些需求时，用这个 skill：

- 用户要通过机器人调用单掌柜 ERP 接口
- 用户要把聊天内容下发到单掌柜，生成订单草稿
- 用户要确认请求地址、认证头、请求体、返回体
- 用户要排查 Dan ERP API 的鉴权或入参问题
- 用户要把新的 Dan ERP API 补进同一个 skill

如果需求和 Dan ERP 开放接口无关，不要用这个 skill。

## Required Config

这个 skill 现在支持在 QClaw / OpenClaw 的 Skill 配置页里直接配置。

需要配置两个值：

- `DAN_ERP_BASE_URL`
  - 例如本地调试：`http://localhost:8000`
  - 例如线上环境：`https://erp.example.com`
- `DAN_ERP_TOKEN`
  - 商户自己的开放接口 token

推荐配置方式：

- 在 Skill 管理页里给 `dan-erp-skill` 填 `API 地址` 和 `Token`
- 配好后，机器人后续调用就不需要每次再问用户

## Working Rules

- 认证一律使用商户自己的 API token，不要复用登录态
- 默认使用 `Authorization: Bearer <token>`
- 兼容 `X-API-Token: <token>`，但优先 Bearer
- 不要在日志、回复、代码片段里回显完整 token
- 只调用已经写在 `references/api_reference.md` 里的接口，不要臆造新接口
- 优先使用 `scripts/dan_erp_client.py` 发请求，减少每次手写 HTTP 细节
- 如果接口返回 401，优先检查 token 是否缺失、写错、商户是否停用
- 如果接口返回 400，优先检查字段名、聊天内容长度、JSON 格式
- 如果缺少配置，优先提示补齐 `DAN_ERP_BASE_URL` 和 `DAN_ERP_TOKEN`

## Quick Start

调用前先准备：

- `DAN_ERP_BASE_URL`
  - 例如本地开发环境：`http://localhost:8000`
- `DAN_ERP_TOKEN`
  - 每个商户单独一份

标准调用方式：

```bash
curl -X POST "${DAN_ERP_BASE_URL}/api/order-drafts/" \
  -H "Authorization: Bearer ${DAN_ERP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_content": "张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒",
    "client_request_id": "req-001",
    "client_name": "crm-sync"
  }'
```

也可以直接用 skill 自带脚本：

```bash
python {baseDir}/scripts/dan_erp_client.py create-order-draft \
  --chat-content "张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒" \
  --client-request-id "req-001" \
  --client-name "crm-sync"
```

如果已经在 Skill 配置里填好 `DAN_ERP_BASE_URL` 和 `DAN_ERP_TOKEN`，脚本不需要再传 `--base-url` 和 `--token`。

## Workflow

### 创建草稿订单

1. 读取 `references/api_reference.md`
2. 确认当前要用的是“草稿订单下发 API”
3. 检查 `DAN_ERP_BASE_URL` 和 `DAN_ERP_TOKEN` 是否已配置
4. 优先用 `scripts/dan_erp_client.py` 或标准 HTTP 请求发起调用
5. 读取返回的 `draft.id` 和解析结果
6. 若失败，按错误码做最小排查

### 扩展新 API

后续 Dan ERP 新增开放接口时，按下面顺序更新 skill：

1. 在 `references/api_reference.md` 新增接口章节
2. 写清楚路径、方法、认证、请求参数、成功返回、常见错误
3. 如果要提供稳定调用方式，就在 `scripts/dan_erp_client.py` 新增对应子命令
4. 保持旧接口说明不变，不要混改现有字段定义
5. 如果新接口需要额外配置，再补充 `metadata.openclaw.requires` 与正文说明

## Current Capability

当前已上线接口只有一个：

- `POST /api/order-drafts/`
  - 提交聊天内容，生成订单草稿

详细字段和返回示例见 [references/api_reference.md](references/api_reference.md)。
