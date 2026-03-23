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

OpenClaw 当前这个 Skill 配置页，默认只会给 skill 的 `primaryEnv` 渲染一个密码框。

对这个 skill 来说，当前能直接在配置页里填写的是：

- `DAN_ERP_TOKEN`
  - 商户开放接口 token

`DAN_ERP_BASE_URL` 仍然支持，但需要按下面的规则处理：

- 如果没配置，脚本默认回退到：`http://localhost:8000`
- 如果 ERP 不在本机，再通过环境变量或命令参数覆盖：
  - `DAN_ERP_BASE_URL=https://erp.example.com`
  - `--base-url https://erp.example.com`

### 给 QClaw 的结构化抽取要求

QClaw 在调用这个 skill 时，不要只把原文直接发给 ERP。

更推荐的方式是：

1. 先从客户聊天内容里提取一组 `prefilled_fields`
2. 再把 `chat_content + prefilled_fields + parse_context` 一起发给 ERP

最低要求：

- 不要省略 `prefilled_fields`
- 如果一个字段都提取不出来，也要传 `prefilled_fields: {}`
- 不要只提交 `chat_content`

`prefilled_fields` 只建议使用这些键：

- `recipient_name`
- `recipient_phone`
- `province`
- `city`
- `district`
- `address_detail`
- `receiver_address`
- `product_text`
- `spec_name`
- `quantity`
- `unit`
- `remark`
- `is_paid`

约束：

- 不能判断的字段就省略，不要编造
- 不要自己补 `sku_code`
- `product_text` 只是客户原话里的商品文本，不代表已经匹配 ERP 商品
- 地址能拆就拆；拆不出来时才传 `receiver_address`
- `quantity` 尽量传数字；看不出数量时不要写默认值
- 如果原文里明确有 `已付款 / 已付 / 已转账 / 已支付`，可以传 `is_paid: true`

推荐让 QClaw 按下面这个固定结构构造请求体：

```json
{
  "chat_content": "<客户聊天原文>",
  "prefilled_fields": {
    "recipient_name": "<如果能判断>",
    "recipient_phone": "<如果能判断>",
    "province": "<如果能判断>",
    "city": "<如果能判断>",
    "district": "<如果能判断>",
    "address_detail": "<如果能判断>",
    "receiver_address": "<如果能判断>",
    "product_text": "<如果能判断>",
    "spec_name": "<如果能判断>",
    "quantity": "<如果能判断>",
    "unit": "<如果能判断>",
    "remark": "<如果能判断>",
    "is_paid": true
  },
  "parse_context": {
    "source": "qclaw",
    "mode": "partial_extract"
  }
}
```

如果没有提取出任何字段，也要保持这个结构：

```json
{
  "chat_content": "<客户聊天原文>",
  "prefilled_fields": {},
  "parse_context": {
    "source": "qclaw",
    "mode": "partial_extract"
  }
}
```

### Base URL

- 本地开发环境：`http://localhost:8000`
- 生产环境：由部署域名决定，例如 `https://你的域名`

如果 skill 运行在装了 Dan ERP 的同一台机器上，而且没有单独配置 `DAN_ERP_BASE_URL`，脚本会默认使用本地这个地址。

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

把外部系统里的聊天内容下发给 Dan ERP，生成一条或多条订单草稿，效果等同于后台页面 `/order-drafts/create/` 的“聊天识别创建草稿”。

### Request Body

支持以下字段：

```json
{
  "chat_content": "录单：张三 13800138000 上海市浦东新区测试路1号 杨梅礼盒 2斤装 2盒",
  "prefilled_fields": {
    "recipient_name": "张三",
    "recipient_phone": "13800138000",
    "province": "上海市",
    "city": "上海市",
    "district": "浦东新区",
    "address_detail": "测试路1号",
    "product_text": "杨梅礼盒",
    "spec_name": "2斤装",
    "quantity": 2,
    "unit": "盒"
  },
  "parse_context": {
    "source": "qclaw",
    "mode": "partial_extract"
  },
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
- `prefilled_fields`
  - 对象，可选
  - 上游 agent 先提取出来的结构化字段
  - 推荐传这些字段：
    - `recipient_name`
    - `recipient_phone`
    - `province`
    - `city`
    - `district`
    - `address_detail`
    - `receiver_address`
    - `product_text`
    - `spec_name`
    - `quantity`
    - `unit`
    - `remark`
    - `is_paid`
  - 单单场景下，这些字段会被服务端当作预填槽位优先复用
  - 多单场景下，这些字段只适合放共享商品信息或通用备注，不要把单个收件人、手机号、地址硬塞给整段多单聊天
  - 商品最终匹配仍由 Dan ERP 服务端完成，不要在这里伪造 SKU
  - 不能判断的字段直接省略，不要写 `null`
  - 即使没有提取出任何字段，也建议显式传空对象 `{}`，不要省略这个键
- `parse_context`
  - 对象，可选
  - 用来标记这批 `prefilled_fields` 的来源和模式
  - 例如：
    - `source: "qclaw"`
    - `mode: "partial_extract"`
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
  "draft_count": 2,
  "drafts": [
    {
      "id": 12,
      "source_type": "api",
      "parse_status": "parsed",
      "customer_name": "张三",
      "receiver_name": "张三",
      "receiver_mobile": "13800138000",
      "receiver_address": "测试路 1 号",
      "province": "上海市",
      "city": "上海市",
      "district": "浦东新区",
      "product_name": "杨梅礼盒",
      "spec_name": "2斤装",
      "quantity": "1",
      "unit": "盒",
      "remark": "",
      "created_at": "2026-03-23T12:34:56+08:00",
      "parsed_result": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "parse_mode": "partial_ai",
        "orders_count": 2,
        "order_index": 1
      }
    },
    {
      "id": 13,
      "source_type": "api",
      "parse_status": "parsed",
      "customer_name": "李四",
      "receiver_name": "李四",
      "receiver_mobile": "13900139000",
      "receiver_address": "和谐路 8 号",
      "province": "江苏省",
      "city": "苏州市",
      "district": "常熟市",
      "product_name": "杨梅礼盒",
      "spec_name": "2斤装",
      "quantity": "1",
      "unit": "盒",
      "remark": "",
      "created_at": "2026-03-23T12:34:56+08:00",
      "parsed_result": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "parse_mode": "partial_ai",
        "orders_count": 2,
        "order_index": 2
      }
    }
  ]
}
```

说明：

- 当前返回结构以 `drafts` 数组和 `draft_count` 为主
- 如果只生成 1 条草稿，服务端会额外兼容返回 `draft`
- 不要再依赖 `confidence_score`，这个字段已经移除
- 订单草稿创建现在以 AI 结果为准；如果 AI 识别失败，接口会直接返回错误，不再自动回退本地规则解析
- 如果 `prefilled_fields` 已经很完整，服务端可能直接复用这些字段，不再做整段 AI 重跑
- 如果 `prefilled_fields` 只补了一部分，服务端会优先保留这些字段，并让 AI 重点补缺失字段
- `parsed_result.parse_mode` 常见值：
  - `prefilled_only`
  - `partial_ai`
  - `full_ai`

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
    "chat_content": "录单：帮我发2份杨梅礼盒2斤装，两个地址各寄一份：上海市浦东新区测试路1号，张三，13800138000；江苏省常熟市和谐路8号，李四，13900139000",
    "prefilled_fields": {
      "product_text": "杨梅礼盒",
      "spec_name": "2斤装",
      "quantity": 2,
      "unit": "盒"
    },
    "parse_context": {
      "source": "qclaw",
      "mode": "partial_extract"
    },
    "client_request_id": "req-001",
    "client_name": "crm-sync"
  }'
```

### Script Example

```bash
python {baseDir}/scripts/dan_erp_client.py create-order-draft \
  --chat-content "录单：帮我发2份杨梅礼盒2斤装，两个地址各寄一份：上海市浦东新区测试路1号，张三，13800138000；江苏省常熟市和谐路8号，李四，13900139000" \
  --prefilled-fields-json '{"product_text":"杨梅礼盒","spec_name":"2斤装","quantity":2,"unit":"盒"}' \
  --client-request-id "req-001" \
  --client-name "crm-sync"
```

如果还没在 Skill 配置里填值，也可以显式传：

```bash
python {baseDir}/scripts/dan_erp_client.py create-order-draft \
  --base-url "http://localhost:8000" \
  --token "merchant-api-token" \
  --chat-content "录单：帮我发2份杨梅礼盒2斤装，两个地址各寄一份：上海市浦东新区测试路1号，张三，13800138000；江苏省常熟市和谐路8号，李四，13900139000"
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
