# 前端契约文档 - agent

> Version: v0.2.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. 请求模型（前端视角）

### 1.1 扩展请求模型

```ts
// POST /api/prereview
interface CreatePreReviewRequest {
  requirementText: string;
  backgroundText?: string;
  businessDomain?: string;
  moduleHint?: string;
  attachments?: Array<{ fileId: string }>;
  debugOptions?: {
    includeTrace?: boolean;
    retrievalMode?: 'dense' | 'sparse' | 'hybrid';
    toolPolicy?: {
      enableTools?: boolean;
      maxToolCalls?: number;
    };
  };
}

// POST /api/prereview/{session_id}/regenerate
interface RegeneratePreReviewRequest {
  additionalContext?: string;
  attachments?: Array<{ fileId: string }>;
  debugOptions?: {
    includeTrace?: boolean;
    retrievalMode?: 'dense' | 'sparse' | 'hybrid';
    toolPolicy?: {
      enableTools?: boolean;
      maxToolCalls?: number;
    };
  };
}
```

### 1.2 管理端请求模型

```ts
// POST /api/admin/agent/reindex
interface AdminReindexRequest {
  sourceIds?: string[];
  forceRebuild?: boolean;
}
```

## 2. 响应模型（前端视图模型）

```ts
interface PreReviewDetailView {
  sessionId: string;
  status: 'PROCESSING' | 'DONE' | 'FAILED';
  summary: string;
  capability: {
    status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'NOT_SUPPORTED' | 'NEED_MORE_INFO';
    reason: string;
    confidence?: 'high' | 'medium' | 'low' | null;
  };
  // 新增 optional 字段
  modelTrace?: {
    provider: string;
    model: string;
    latencyMs: number;
    totalTokens?: number;
    costUsd?: number;
    fallbackPath?: string[];
  } | null;
  retrievalTrace?: {
    mode: 'dense' | 'sparse' | 'hybrid';
    backend: string;
    denseHits: number;
    sparseHits: number;
    fusedHits: number;
    reranker?: string;
    latencyMs: number;
  } | null;
  toolTrace?: Array<{
    toolName: string;
    status: 'SUCCESS' | 'FAILED' | 'TIMEOUT' | 'SKIPPED';
    latencyMs: number;
    argsSummary?: string;
    errorCode?: string;
  }> | null;
}

interface AgentRuntimeResponse {
  model: {
    mode: 'heuristic' | 'cloud';
    primaryProvider: string;
    fallbackProviders: string[];
  };
  rag: {
    mode: 'legacy' | 'layered';
    backend: 'sqlite' | 'postgres_pgvector';
    retrievers: string[];
    reranker?: string;
  };
}

interface AgentReindexResponse {
  jobId: string;
  status: 'QUEUED' | 'RUNNING' | 'DONE' | 'FAILED';
}
```

## 3. 状态与枚举映射

| 后端枚举 | 前端枚举 | 说明 |
|---|---|---|
| `PROCESSING/DONE/FAILED` | 同名 | 任务状态 |
| `SUPPORTED/PARTIALLY_SUPPORTED/NOT_SUPPORTED/NEED_MORE_INFO` | 同名 | 能力结论 |
| `dense/sparse/hybrid` | 同名 | 检索模式 |
| `QUEUED/RUNNING/DONE/FAILED` | 同名 | reindex 任务状态 |

兼容策略：

1. 未识别的 `retrievalMode` 回退为 `hybrid`。
2. 缺失 `modelTrace/retrievalTrace` 时渲染为 `null`。
3. 缺失 `toolTrace` 时渲染为空数组或 `null`。

## 4. 错误码到 UI 行为映射

| error_code | UI 行为 |
|---|---|
| `MODEL_TIMEOUT` | 提示“模型超时”，支持重试 |
| `MODEL_RATE_LIMIT` | 提示“请求限流”，建议稍后重试 |
| `MODEL_SCHEMA_ERROR` | 提示“模型结果异常”，显示保守结论 |
| `RAG_INDEX_UNAVAILABLE` | 提示“检索索引不可用”，允许降级继续 |
| `RAG_QUERY_INVALID` | 标记 debug 参数非法并回退默认 |
| `TOOL_EXECUTION_ERROR` | 提示“工具执行失败”，显示降级结果 |
| `TOOL_TIMEOUT` | 提示“工具调用超时”，建议重试 |
| `PERMISSION_DENIED` | 管理按钮禁用 + toast |
| `WORKFLOW_ERROR` | 详情页失败态 |

## 5. 与后端契约对齐说明

1. 新增字段均 optional，不影响旧前端/后端互通。
2. debugOptions 仅在发送时生效，后端可忽略不支持字段。
> Obsolete in v0.2.0: `debugOptions` 仅含 `includeTrace/retrievalMode`。  
> Replacement in v0.2.0: 扩展 `debugOptions.toolPolicy`，用于 Tool 执行预算控制。
3. runtime/reindex 接口仅管理角色可调用。

## 6. 接口明细（FC-*）

### FC-001
GET /api/agent/runtime

- 权限：`OWNER/ADMIN`
- 请求：无
- 响应：`AgentRuntimeResponse`
- 失败：`401 AUTH_ERROR`、`403 PERMISSION_DENIED`

示例响应：

```json
{
  "model": {
    "mode": "cloud",
    "primaryProvider": "openai",
    "fallbackProviders": ["anthropic"]
  },
  "rag": {
    "mode": "layered",
    "backend": "postgres_pgvector",
    "retrievers": ["dense", "sparse"],
    "reranker": "cross_encoder_bge"
  }
}
```

### FC-002
POST /api/admin/agent/reindex

- 权限：`OWNER/ADMIN`
- 请求：`AdminReindexRequest`
- 响应：`AgentReindexResponse`
- 失败：`403 PERMISSION_DENIED`、`422 VALIDATION_ERROR`

示例请求：

```json
{
  "sourceIds": ["src_product_docs"],
  "forceRebuild": false
}
```

### FC-003
POST /api/prereview

- 权限：`OWNER/ADMIN/MEMBER`
- 请求：`CreatePreReviewRequest`
- 响应：`{ sessionId: string; status: "PROCESSING" }`
- 兼容：`debugOptions` 可省略

### FC-004
POST /api/prereview/{session_id}/regenerate

- 权限：`OWNER/ADMIN/MEMBER`
- 请求：`RegeneratePreReviewRequest`
- 响应：`{ sessionId: string; status: "PROCESSING" }`
- 失败：`404 VALIDATION_ERROR`（父会话不存在）

### FC-005
GET /api/prereview/{session_id}

- 权限：已登录
- 请求：路径参数 `session_id`
- 响应：`PreReviewDetailView`（含 optional trace）
- 失败：`404 VALIDATION_ERROR`、`500 WORKFLOW_ERROR`
