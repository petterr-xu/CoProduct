# 后端契约文档 - agent

> Version: v0.2.0
> Last Updated: 2026-03-13
> Status: Draft

## 1. API 列表（Method + Path）

1. GET /api/agent/runtime
2. POST /api/admin/agent/reindex
3. POST /api/prereview
4. POST /api/prereview/{session_id}/regenerate
5. GET /api/prereview/{session_id}

## 2. 请求结构与校验规则

### BC-001
GET /api/agent/runtime

- 请求体：无
- 校验：无

### BC-002
POST /api/admin/agent/reindex

请求体：

```json
{
  "sourceIds": ["src_product_docs"],
  "forceRebuild": false
}
```

字段规则：

| 字段 | 类型 | 必填 | 校验 |
|---|---|---|---|
| `sourceIds` | string[] | 否 | 每项非空，长度 <= 128 |
| `forceRebuild` | bool | 否 | 默认 false |

### BC-003
POST /api/prereview

新增可选字段：

```json
{
  "debugOptions": {
    "includeTrace": true,
    "retrievalMode": "hybrid"
  }
}
```

字段规则：

| 字段 | 类型 | 必填 | 校验 |
|---|---|---|---|
| `debugOptions.includeTrace` | bool | 否 | 默认 false |
| `debugOptions.retrievalMode` | enum | 否 | `dense/sparse/hybrid` |
| `debugOptions.toolPolicy.enableTools` | bool | 否 | 默认 true |
| `debugOptions.toolPolicy.maxToolCalls` | int | 否 | `1~5`，默认 3 |

### BC-004
POST /api/prereview/{session_id}/regenerate

新增可选字段同 BC-003。

### BC-005
GET /api/prereview/{session_id}

- 请求参数：`session_id` (path)
- 校验：非空字符串

## 3. 响应结构与字段语义

### 3.1 GET /api/agent/runtime

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

字段语义：

| 字段 | 语义 |
|---|---|
| `model.mode` | 当前模型运行模式（heuristic/cloud） |
| `model.primaryProvider` | 主 provider |
| `model.fallbackProviders` | 依次降级 provider 列表 |
| `rag.mode` | 检索模式（legacy/layered） |
| `rag.backend` | 索引后端 |
| `rag.retrievers` | 生效检索器列表 |
| `rag.reranker` | 生效重排器 |

### 3.2 POST /api/admin/agent/reindex

```json
{
  "jobId": "job_abc123",
  "status": "QUEUED"
}
```

### 3.3 GET /api/prereview/{session_id}

在现有响应中新增 optional 字段：

```json
{
  "modelTrace": {
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "latencyMs": 812,
    "totalTokens": 2134,
    "costUsd": 0.012,
    "fallbackPath": ["openai"]
  },
  "retrievalTrace": {
    "mode": "hybrid",
    "backend": "postgres_pgvector",
    "denseHits": 20,
    "sparseHits": 20,
    "fusedHits": 24,
    "reranker": "cross_encoder_bge",
    "latencyMs": 146
  },
  "toolTrace": [
    {
      "toolName": "retrieve_knowledge",
      "status": "SUCCESS",
      "latencyMs": 52,
      "argsSummary": "mode=hybrid, topK=20"
    }
  ]
}
```

## 4. 状态/错误码规则

| 场景 | HTTP | error_code |
|---|---|---|
| 未登录/令牌失效 | 401 | `AUTH_ERROR` / `TOKEN_EXPIRED` |
| 无管理权限调用 runtime/reindex | 403 | `PERMISSION_DENIED` |
| reindex 参数错误 | 422 | `VALIDATION_ERROR` |
| 云模型超时 | 500 | `MODEL_TIMEOUT` |
| 模型限流 | 429/500 | `MODEL_RATE_LIMIT` |
| 模型结构化失败 | 500 | `MODEL_SCHEMA_ERROR` |
| 检索索引不可用 | 503/500 | `RAG_INDEX_UNAVAILABLE` |
| 工具执行失败 | 500 | `TOOL_EXECUTION_ERROR` |
| 工具执行超时 | 504/500 | `TOOL_TIMEOUT` |
| 预审流程异常 | 500 | `WORKFLOW_ERROR` |

## 5. 权限与数据范围规则

1. GET /api/agent/runtime：`OWNER/ADMIN`。
2. POST /api/admin/agent/reindex：`OWNER/ADMIN`。
3. POST /api/prereview：`OWNER/ADMIN/MEMBER`。
4. POST /api/prereview/{session_id}/regenerate：`OWNER/ADMIN/MEMBER`。
5. GET /api/prereview/{session_id}：组织内可读，`MEMBER` 仅可读本人创建会话。

## 6. 与前端契约对齐说明

1. FC/BC endpoint 集合完全一致（5 条）。
2. trace 字段 optional，兼容旧前端与旧数据。
> Obsolete in v0.2.0: 详情 trace 仅定义 model/retrieval 两类。  
> Replacement in v0.2.0: 增加 `toolTrace`，用于可观测 Tool 执行链路。
3. 枚举域保持一致：`retrievalMode` 与任务状态枚举不可漂移。
