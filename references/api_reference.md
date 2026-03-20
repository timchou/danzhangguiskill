# Dan ERP API Reference

## 通用约定

### 推荐使用口径

为了让机器人更稳定地调用这个 skill，建议商家统一使用：

```text
录单：客户聊天内容
```

例如：

```text
录单：张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒
```

如果是多行内容，也可以：

```text
录单
张三 13800138000 上海市浦东新区测试路1号
杨梅礼盒 2斤装 2盒
```

### QClaw / OpenClaw 配置

建议在 Skill 配置页直接填写这两个值：

- `DAN_ERP_BASE_URL`
  - ERP 服务地址
  - 本地调试例子：`http://localhost:8000`
  - 线上例子：`https://erp.example.com`
- `DAN_ERP_TOKEN`
  - 商户开放接口 token

配置完成后，skill 脚本会自动读取这两个环境变量。

### Base URL

- 本地开发环境：`http://localhost:8000`
- 生产环境：由部署域名决定，例如 `https://你的域名`

### 认证

优先使用：

```http
Authorization: Bearer <merchant_api_token>
```

兼容：

```http
X-API-Token: <merchant_api_token>
```

说明：

- token 是商户级别，不是员工账号级别
- 每个商户一份，单独发放
- token 缺失或错误会返回 `401`
- 商户停用会返回 `403`

### Content-Type

请求体使用 JSON：

```http
Content-Type: application/json
```

### 错误处理

- `400`
  - 请求体不是合法 JSON
  - 缺少必要字段
  - 聊天内容太短
  - 商户没配置可用 AI
- `401`
  - 缺少 token
  - token 无效
- `403`
  - 商户已停用
- `500`
  - 服务端异常，请稍后重试

## 1. 创建订单草稿

### Endpoint

```http
POST /api/order-drafts/
```

### 用途

把外部系统里的聊天内容下发给 Dan ERP，生成一条订单草稿，效果等同于后台页面 `/order-drafts/create/` 的“聊天识别创建草稿”。

### Request Body

支持以下字段：

```json
{
  "chat_content": "录单：张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒",
  "client_request_id": "req-001",
  "client_name": "crm-sync"
}
```

字段说明：

- `chat_content`
  - 字符串，推荐字段名
  - 聊天内容原文
  - 建议保留 `录单：` 前缀
  - 长度至少 8 个字符
- `source_raw_text`
  - 字符串，兼容字段名
  - 如果传了 `chat_content`，优先取 `chat_content`
- `client_request_id`
  - 字符串，可选
  - 调用方自己的请求编号
  - 会落到草稿的 `source_message_id`
- `client_name`
  - 字符串，可选
  - 调用方系统名
  - 会落到草稿的 `source_payload.client_name`

### Success Response

状态码：

```http
201 Created
```

返回示例：

```json
{
  "ok": true,
  "merchant_code": "api-demo",
  "draft": {
    "id": 12,
    "source_type": "api",
    "parse_status": "parsed",
    "confidence_score": "0.93",
    "customer_name": "张三",
    "receiver_name": "张三",
    "receiver_mobile": "13800138000",
    "receiver_address": "上海市浦东新区测试路 1 号",
    "province": "上海市",
    "city": "上海市",
    "district": "浦东新区",
    "product_name": "杨梅礼盒",
    "spec_name": "2斤装",
    "quantity": "2",
    "unit": "盒",
    "remark": "尽快发货",
    "created_at": "2026-03-20T12:34:56+08:00",
    "parsed_result": {
      "provider": "deepseek",
      "model": "deepseek-chat"
    }
  }
}
```

### Failure Responses

缺少 token：

```json
{
  "ok": false,
  "error": "缺少 API Token。"
}
```

token 无效：

```json
{
  "ok": false,
  "error": "API Token 无效。"
}
```

缺少聊天内容：

```json
{
  "ok": false,
  "error": "缺少聊天内容。"
}
```

聊天内容过短：

```json
{
  "ok": false,
  "error": "聊天内容过短，无法生成草稿。"
}
```

商户已停用：

```json
{
  "ok": false,
  "error": "商户已停用，无法调用接口。"
}
```

服务端异常：

```json
{
  "ok": false,
  "error": "服务端异常，请稍后重试。"
}
```

### curl Example

```bash
curl -X POST "${DAN_ERP_BASE_URL}/api/order-drafts/" \
  -H "Authorization: Bearer ${DAN_ERP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_content": "录单：张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒",
    "client_request_id": "req-001",
    "client_name": "crm-sync"
  }'
```

### Script Example

```bash
python {baseDir}/scripts/dan_erp_client.py create-order-draft \
  --chat-content "录单：张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒" \
  --client-request-id "req-001" \
  --client-name "crm-sync"
```

如果还没在 Skill 配置里填值，也可以显式传：

```bash
python {baseDir}/scripts/dan_erp_client.py create-order-draft \
  --base-url "http://localhost:8000" \
  --token "merchant-api-token" \
  --chat-content "录单：张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒"
```

## 新接口补充模板

后续新增接口时，按下面格式继续补：

```md
## N. 接口名称

### Endpoint
POST /api/xxx/

### 用途

### Request Body

### Success Response

### Failure Responses

### curl Example
```
