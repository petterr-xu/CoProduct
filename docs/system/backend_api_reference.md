# 后端 API 参考（重要接口详解）
> Version: v0.1.1
> Last Updated: 2026-03-12
> Status: Active

## 1. 基础约定

## 1.1 Base URL

默认本地：`http://localhost:8000`

## 1.2 鉴权

所有业务接口都需要：

```http
Authorization: Bearer <COPRODUCT_API_TOKEN>
```

鉴权失败示例：

```json
{
  "detail": {
    "error_code": "AUTH_ERROR",
    "message": "Missing Authorization header"
  }
}
```

## 1.3 通用错误体字段

| 字段 | 类型 | 作用 |
|---|---|---|
| `error_code` | string | 稳定错误码，用于前端分支处理与日志筛选 |
| `message` | string | 人类可读错误信息 |
| `status` | string | 仅部分场景存在（如 404 的 `NOT_FOUND`） |

## 1.4 状态口径

1. Session 状态：`PROCESSING | DONE | FAILED`
2. `NOT_FOUND` 仅出现在 404 错误体，不属于持久化 session 状态。

---

## 2. 健康检查

## `GET /healthz`

响应：

```json
{"status": "ok"}
```

字段说明：

| 字段 | 类型 | 作用 |
|---|---|---|
| `status` | string | 服务存活标识，当前固定为 `ok` |

---

## 3. 预审接口

## 3.1 创建预审

### `POST /api/prereview`

请求体：

```json
{
  "requirementText": "运营希望按活动导出报名信息",
  "backgroundText": "当前需要人工 SQL",
  "businessDomain": "activity",
  "moduleHint": "export_service",
  "attachments": [{ "fileId": "file_xxx" }]
}
```

请求字段说明：

| 字段 | 类型 | 必填 | 作用 |
|---|---|---|---|
| `requirementText` | string | 是 | 需求主体描述，工作流核心输入 |
| `backgroundText` | string | 否 | 背景上下文，进入 `merged_text` |
| `businessDomain` | string | 否 | 业务域提示，辅助检索规划 |
| `moduleHint` | string | 否 | 模块提示，辅助检索过滤 |
| `attachments` | array | 否 | 附件引用列表，仅传 `fileId` |
| `attachments[].fileId` | string | 否 | 已上传文件的稳定引用 ID |

成功响应：

```json
{
  "sessionId": "ses_xxxxx",
  "status": "PROCESSING"
}
```

响应字段说明：

| 字段 | 类型 | 作用 |
|---|---|---|
| `sessionId` | string | 本次预审会话 ID，后续查询与再生成都依赖它 |
| `status` | string | 当前会话状态，创建后固定先返回 `PROCESSING` |

错误码：

1. `WORKFLOW_ERROR`（500）

---

## 3.2 查询预审详情

### `GET /api/prereview/{session_id}`

成功响应（字段级 view model）：

```json
{
  "sessionId": "ses_xxx",
  "parentSessionId": "ses_parent_or_null",
  "version": 2,
  "status": "DONE",
  "summary": "...",
  "capability": {
    "status": "PARTIALLY_SUPPORTED",
    "reason": "...",
    "confidence": "medium"
  },
  "evidence": [
    {
      "doc_id": "kdoc_xxx",
      "doc_title": "导出 API 说明",
      "chunk_id": "kchk_xxx",
      "snippet": "...",
      "source_type": "api_doc",
      "relevance_score": 0.91,
      "trust_level": "HIGH"
    }
  ],
  "structuredRequirement": {
    "goal": "支持导出能力",
    "actors": ["运营"],
    "scope": ["导出任务"],
    "constraints": ["角色权限边界"],
    "expectedOutput": "导出文件"
  },
  "missingInfo": ["..."],
  "risks": [{"title":"security","description":"...","level":"high"}],
  "impactScope": ["export_service: 导出能力相关"],
  "nextActions": ["..."],
  "uncertainties": ["..."],
  "evidenceCount": 3,
  "errorCode": null,
  "errorMessage": null
}
```

响应字段说明（核心）：

| 字段 | 类型 | 作用 |
|---|---|---|
| `sessionId` | string | 当前会话唯一标识 |
| `parentSessionId` | string/null | 父会话 ID（再生成场景） |
| `version` | number | 会话版本号（首次为 1） |
| `status` | enum | 会话执行状态 |
| `summary` | string | 结果摘要 |
| `capability` | object | 能力判断主结论 |
| `capability.status` | enum | `SUPPORTED/PARTIALLY_SUPPORTED/NOT_SUPPORTED/NEED_MORE_INFO` |
| `capability.reason` | string | 结论原因 |
| `capability.confidence` | enum | 置信度 `high/medium/low` |
| `evidence` | array | 证据明细列表 |
| `structuredRequirement` | object | 结构化需求草案 |
| `missingInfo` | array | 需补充问题列表 |
| `risks` | array | 风险条目列表 |
| `impactScope` | array | 影响范围描述 |
| `nextActions` | array | 下一步建议 |
| `uncertainties` | array | 不确定项 |
| `evidenceCount` | number | 证据条目数量（持久化层统计） |
| `errorCode` | string/null | 会话失败时的错误码（当前主要 `WORKFLOW_ERROR`） |
| `errorMessage` | string/null | 会话失败时错误描述 |

404 响应：

```json
{
  "detail": {
    "error_code": "VALIDATION_ERROR",
    "message": "session not found",
    "status": "NOT_FOUND"
  }
}
```

---

## 3.3 再生成

### `POST /api/prereview/{session_id}/regenerate`

请求体：

```json
{
  "additionalContext": "补充：仅主管可导出手机号",
  "attachments": [{ "fileId": "file_xxx" }]
}
```

请求字段说明：

| 字段 | 类型 | 必填 | 作用 |
|---|---|---|---|
| `additionalContext` | string | 否 | 对历史需求补充说明，参与重新推理 |
| `attachments` | array | 否 | 本次再生成附加的文件引用 |
| `attachments[].fileId` | string | 否 | 文件引用 ID，用于读取并并入文本 |

行为说明：

1. 创建新 session（不覆盖历史）。
2. 新 session 版本号 +1，并记录 `parentSessionId`。
3. 重走完整工作流。

成功响应：

```json
{
  "sessionId": "ses_new_xxx",
  "status": "PROCESSING"
}
```

错误码：

1. `VALIDATION_ERROR`（404，父 session 或 request 不存在）
2. `WORKFLOW_ERROR`（500）

---

## 4. 文件接口

## 4.1 上传附件

### `POST /api/files/upload`

请求类型：`multipart/form-data`，字段名 `file`。

成功响应：

```json
{
  "fileId": "file_xxx",
  "fileName": "a.txt",
  "fileSize": 1234,
  "parseStatus": "PENDING"
}
```

响应字段说明：

| 字段 | 类型 | 作用 |
|---|---|---|
| `fileId` | string | 文件引用 ID（create/regenerate 均使用该 ID） |
| `fileName` | string | 原始文件名，用于展示 |
| `fileSize` | number | 文件字节大小，用于前端大小控制 |
| `parseStatus` | enum | 解析状态（`PENDING/PARSING/DONE/FAILED`） |

状态语义：

1. `PENDING`：上传完成，待解析。
2. `PARSING`：解析中。
3. `DONE`：解析完成，可并入输入。
4. `FAILED`：解析失败，可重传或忽略。

约束：

1. 允许扩展名：`.txt/.md/.pdf/.docx`
2. 大小上限：`COPRODUCT_UPLOAD_MAX_SIZE_MB`

常见错误：

1. `FILE_UPLOAD_ERROR: unsupported file type`
2. `FILE_UPLOAD_ERROR: file too large`
3. `FILE_UPLOAD_ERROR`（500，上传过程失败）

---

## 5. 历史接口

## 5.1 历史查询

### `GET /api/history`

Query 参数：

| 参数 | 类型 | 必填 | 作用 |
|---|---|---|---|
| `keyword` | string | 否 | 需求关键字过滤（匹配 requirement/background） |
| `capabilityStatus` | enum | 否 | 按能力结论过滤 |
| `page` | number | 否 | 页码，默认 1，最小 1 |
| `pageSize` | number | 否 | 每页大小，默认 20，范围 1~100 |

示例：

```http
GET /api/history?keyword=导出&capabilityStatus=SUPPORTED&page=1&pageSize=20
```

响应：

```json
{
  "total": 15,
  "page": 1,
  "pageSize": 20,
  "items": [
    {
      "sessionId": "ses_xxx",
      "requestText": "支持导出报名记录",
      "capabilityStatus": "SUPPORTED",
      "version": 1,
      "createdAt": "2026-03-12T08:00:00+00:00"
    }
  ]
}
```

响应字段说明：

| 字段 | 类型 | 作用 |
|---|---|---|
| `total` | number | 满足条件的总记录数 |
| `page` | number | 当前页码 |
| `pageSize` | number | 每页条数 |
| `items` | array | 当前页数据 |
| `items[].sessionId` | string | 会话 ID |
| `items[].requestText` | string | 原始需求文本（摘要展示） |
| `items[].capabilityStatus` | enum | 能力结论 |
| `items[].version` | number | 会话版本 |
| `items[].createdAt` | string | 创建时间（ISO 时间串） |

排序：默认按创建时间倒序（新 -> 旧）。

---

## 6. 错误码一览（当前实现）

| 错误码 | 常见来源 | HTTP |
|---|---|---|
| `AUTH_ERROR` | token 缺失或不匹配 | 401 |
| `VALIDATION_ERROR` | 资源不存在、参数不合法 | 404/400 |
| `WORKFLOW_ERROR` | 工作流执行异常 | 500 |
| `FILE_UPLOAD_ERROR` | 文件类型、大小或上传失败 | 400/500 |
| `FILE_PARSE_ERROR` | 附件解析阶段失败（日志/业务提示） | 400（部分场景） |
| `PERSISTENCE_ERROR` | 文档契约保留，当前代码主要以 `WORKFLOW_ERROR` 暴露 | - |

---

## 7. 与前端契约的关键对齐点

1. 详情接口是字段级视图，不返回裸 `report`。
2. 状态枚举以 `PROCESSING/DONE/FAILED` 为准。
3. `capability.confidence` 必须可消费。
4. 上传返回必须含 `parseStatus`，便于前端展示附件状态。
5. regenerate 支持 `attachments` 输入。
