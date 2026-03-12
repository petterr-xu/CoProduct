Title: PreReview Agent Module
Version: v1.0.0
Last Updated: 2026-03-13
Scope: 需求预审主链路（API + Workflow + Persistence）
Audience: Backend/frontend engineers, AI workflow maintainers

# PreReview Agent Module

## Module Goal and Value

预审模块负责把原始需求输入转化为可执行的结构化报告：

1. 把需求文本与附件信息归一化。
2. 通过工作流节点生成结构化需求、能力判断、风险影响、下一步建议。
3. 以稳定读模型返回前端，支持详情展示、轮询和再生成。

## Boundaries and Dependencies

边界内：

1. API: `prereview.py`, `history.py`, `files.py`
2. Service: `PreReviewService`, `PersistenceService`, `SessionService`, `AttachmentService`, `FileService`, `HistoryService`
3. Workflow: `workflow/graph.py` + 11 个节点
4. Repository: `PreReviewRepository`

边界外：

1. 用户身份治理规则（admin/auth 模块）
2. 模型提供者实现细节（model_client）

依赖关系：

1. 鉴权依赖 `get_current_user + require_write_permission`。
2. 检索依赖 `HybridSearcher`。
3. 数据落库依赖 `requests/sessions/reports/evidence/uploaded_files`。

## Core Flow (Mermaid)

```mermaid
flowchart LR
    A[POST /api/prereview]
    B[PreReviewService.create_prereview]
    C[create request + session]
    D[merge attachment text]
    E[LangGraph invoke]
    F[input_normalizer]
    G[requirement_parser]
    H[retrieval_planner]
    I[knowledge_retriever]
    J[evidence_selector]
    K[capability_judge]
    L[missing_info/risk/impact]
    M[report_composer]
    N[persistence_node]
    O[PersistenceService.persist_workflow_result]

    A --> B --> C --> D --> E
    E --> F --> G --> H --> I --> J --> K --> L --> M --> N --> O
```

### Diagram Notes

1. `persistence_node` 只返回状态，真正 DB 持久化由 `PersistenceService` 完成。
2. `risk_analyzer` 与 `impact_analyzer` 具备降级策略，失败时返回空列表。

## API Design

### Endpoint List

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/prereview` | 创建预审任务 |
| GET | `/api/prereview/{session_id}` | 查询预审详情视图 |
| POST | `/api/prereview/{session_id}/regenerate` | 基于父会话再生成 |
| GET | `/api/history` | 查询预审历史分页 |
| POST | `/api/files/upload` | 上传附件，返回 `fileId` |

### Authentication and Authorization

1. `POST /api/prereview`、`POST /regenerate`、`POST /files/upload` 要求写权限角色：`OWNER/ADMIN/MEMBER`。
2. `GET /api/prereview/{id}` 与 `GET /api/history` 需要已登录用户。
3. `PreReviewRepository` 自动按 `org_id` 做范围过滤，`MEMBER` 只能访问自己创建的数据。

### Request Schema and Validation

#### Create PreReview

| Field | Type | Validation | Meaning |
|---|---|---|---|
| `requirementText` | string | required, min 1 | 原始需求描述 |
| `backgroundText` | string | optional | 背景信息 |
| `businessDomain` | string | optional | 业务域提示 |
| `moduleHint` | string | optional | 模块提示，用于检索过滤 |
| `attachments[].fileId` | string | optional | 已上传附件引用 |

#### Regenerate

| Field | Type | Validation | Meaning |
|---|---|---|---|
| `additionalContext` | string | optional | 再生成补充信息 |
| `attachments[].fileId` | string | optional | 再生成附加附件 |

#### History Query

| Field | Type | Validation | Meaning |
|---|---|---|---|
| `keyword` | string | optional | 需求文本模糊过滤 |
| `capabilityStatus` | enum | optional | 能力结论过滤 |
| `page` | int | `>=1` | 页码 |
| `pageSize` | int | `1~100` | 每页大小 |

#### File Upload

| Field | Validation |
|---|---|
| `multipart file` | 扩展名限制：`.txt/.md/.pdf/.docx` |
| file size | `<= COPRODUCT_UPLOAD_MAX_SIZE_MB` |

> 注意：当前附件解析仅支持 `.txt/.md`；`.pdf/.docx` 可上传但解析会标记失败。

### Response Schema and Field Semantics

#### Create/Regenerate Response

| Field | Meaning |
|---|---|
| `sessionId` | 新创建会话 ID |
| `status` | 当前返回固定为 `PROCESSING`（前端据此轮询） |

#### Detail Response (`GET /api/prereview/{session_id}`)

| Field | Meaning |
|---|---|
| `sessionId/parentSessionId/version` | 会话标识与版本关系 |
| `status` | `PROCESSING/DONE/FAILED` |
| `summary` | 报告摘要 |
| `capability.status` | `SUPPORTED/PARTIALLY_SUPPORTED/NOT_SUPPORTED/NEED_MORE_INFO` |
| `capability.reason` | 结论原因 |
| `capability.confidence` | `high/medium/low` |
| `structuredRequirement` | 结构化需求视图 |
| `evidence` | 证据条目数组 |
| `missingInfo/risks/impactScope/nextActions/uncertainties` | 各分析维度输出 |
| `errorCode/errorMessage` | 失败态排障信息 |

#### History Response

统一分页：`items/total/page/pageSize`。

`items` 关键字段：

1. `sessionId`
2. `requestText`
3. `capabilityStatus`
4. `version`
5. `createdAt`

### Error Model and Status Mapping

| Error Code | HTTP Status | Trigger |
|---|---|---|
| `WORKFLOW_ERROR` | 500 | 工作流执行异常 |
| `VALIDATION_ERROR` | 404/422 | session 不存在或参数不合法 |
| `FILE_UPLOAD_ERROR` | 400/500 | 上传类型/大小错误或写盘失败 |
| `FILE_PARSE_ERROR` | 400 | 附件解析失败（服务内部记录） |
| `PERMISSION_DENIED` | 403 | 角色无写权限 |

## Data Model

### Entity List

1. `requests`
2. `sessions`
3. `reports`
4. `evidence_items`
5. `uploaded_files`

### Field Meaning and Constraints

#### `requests`

| Field | Meaning |
|---|---|
| `requirement_text` | 原始需求文本 |
| `background_text` | 背景信息 |
| `business_domain/module_hint` | 检索辅助字段 |
| `org_id` | 数据组织归属 |
| `created_by_user_id` | 创建用户 |

#### `sessions`

| Field | Meaning | Constraint |
|---|---|---|
| `request_id` | 关联 request | FK requests |
| `parent_session_id` | 再生成父会话 | nullable |
| `version` | 会话版本号 | 父版本 +1 |
| `status` | 执行状态 | PROCESSING/DONE/FAILED |
| `error_message` | 失败错误信息 | nullable |

#### `reports`

| Field | Meaning | Constraint |
|---|---|---|
| `session_id` | 所属会话 | unique + FK sessions |
| `summary` | 摘要 |
| `capability_status` | 历史筛选关键字段 |
| `report_json` | 完整结构化报告 JSON |

#### `evidence_items`

字段包含 `doc_id/chunk_id/snippet/relevance_score/source_type/trust_level`，用于报告证据展示。

#### `uploaded_files`

| Field | Meaning |
|---|---|
| `storage_key` | 物理落盘路径 |
| `parse_status` | `PENDING/PARSING/DONE/FAILED` |
| `org_id/created_by_user_id` | 多租户与成员隔离字段 |

### Index / Uniqueness and Relation Notes

1. `sessions.request_id` 支撑按请求查会话版本。
2. `reports.session_id` 唯一确保“一会话一报告快照”。
3. `uploaded_files.org_id/created_by_user_id` 参与 scope 过滤。

### State / Lifecycle Transitions

1. session: `PROCESSING -> DONE` 或 `PROCESSING -> FAILED`。
2. uploaded file: `PENDING -> PARSING -> DONE/FAILED`。
3. regenerate: 基于 parent session 创建 child session，version 递增。

### Retention and Archival

1. 当前无自动清理策略。
2. 历史查询直接读取持久化结果，长期存储策略由后续运维方案定义。

## Failure and Fallback

1. 工作流全链路异常：session 状态写 `FAILED`，并返回 `WORKFLOW_ERROR`。
2. `risk_analyzer`/`impact_analyzer` 异常：降级为空列表，避免整链路中断。
3. `capability_judge` 守门策略：高质量证据不足时降级结论，避免“无证据强支持”。
4. 附件缺失或解析异常：记录日志，跳过该附件文本，不阻断主流程。

## Extension Points

1. `workflow/graph.py` 可引入并行子图（如 risk/impact 并行）。
2. `model_client/factory.py` 可接入云端 LLM 与 embedding 服务。
3. `AttachmentService` 可扩展 `.pdf/.docx` 真正解析器。
4. 可增加异步任务队列实现“长任务异步化 + 回调/通知”。
