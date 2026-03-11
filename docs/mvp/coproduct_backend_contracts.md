# CoProduct 后端契约清单（接口 + 状态 + 节点 I/O）

## 1. 目的

- 固定 API 与 Workflow 的输入输出契约，避免边开发边改协议。
- 本文作为后端、前端、测试共同对齐基线。

---

## 2. API 契约（最终版）

## 2.1 `POST /api/prereview`

请求体：

```json
{
  "requirementText": "string",
  "backgroundText": "string",
  "businessDomain": "string",
  "moduleHint": "string",
  "attachments": [{ "fileId": "string" }]
}
```

响应体：

```json
{
  "sessionId": "string",
  "status": "PROCESSING"
}
```

错误码：`VALIDATION_ERROR` `WORKFLOW_ERROR` `PERSISTENCE_ERROR`

## 2.2 `GET /api/prereview/{session_id}`

响应体（核心字段）：

```json
{
  "sessionId": "string",
  "parentSessionId": "string|null",
  "version": 1,
  "status": "PROCESSING|DONE|FAILED",
  "summary": "string",
  "capability": {
    "status": "SUPPORTED|PARTIALLY_SUPPORTED|NOT_SUPPORTED|NEED_MORE_INFO",
    "reason": "string",
    "confidence": "high|medium|low"
  },
  "evidence": [
    {
      "doc_id": "string",
      "doc_title": "string",
      "chunk_id": "string",
      "snippet": "string",
      "source_type": "product_doc|api_doc|constraint_doc|case",
      "relevance_score": 0.0,
      "trust_level": "HIGH|MEDIUM|LOW"
    }
  ],
  "structuredRequirement": {
    "goal": "string",
    "actors": ["string"],
    "scope": ["string"],
    "constraints": ["string"],
    "expectedOutput": "string"
  },
  "missingInfo": ["string"],
  "risks": [{ "title": "string", "description": "string", "level": "high|medium|low" }],
  "impactScope": ["string"],
  "nextActions": ["string"],
  "uncertainties": ["string"],
  "evidenceCount": 0,
  "errorCode": "string|null",
  "errorMessage": "string|null"
}
```

补充说明：

1. `NOT_FOUND` 只作为 404 错误体中的 `detail.status`，不属于 session 持久化状态枚举。
2. 后端不直接返回 `report` 原始对象，统一返回前端可消费的字段级 view model。

错误码：`VALIDATION_ERROR` `PERSISTENCE_ERROR`

## 2.3 `POST /api/prereview/{session_id}/regenerate`

请求体：

```json
{
  "additionalContext": "string",
  "attachments": [{ "fileId": "string" }]
}
```

响应体：

```json
{
  "sessionId": "string",
  "status": "PROCESSING"
}
```

行为契约：

1. 必须创建新 session
2. `version = old.version + 1`
3. `parent_session_id = old.session_id`
4. 重走完整 workflow

## 2.4 `GET /api/history`

查询参数：

- `keyword`
- `capabilityStatus`
- `page`
- `pageSize`

响应体（示意）：

```json
{
  "total": 0,
  "page": 1,
  "pageSize": 20,
  "items": [
    {
      "sessionId": "string",
      "requestText": "string",
      "capabilityStatus": "SUPPORTED",
      "version": 1,
      "createdAt": "2026-03-10T00:00:00Z"
    }
  ]
}
```

## 2.5 `POST /api/files/upload`

响应体：

```json
{
  "fileId": "string",
  "fileName": "string",
  "parseStatus": "PENDING"
}
```

错误码：`FILE_UPLOAD_ERROR` `FILE_PARSE_ERROR`

---

## 3. Workflow State 契约（固定）

```python
class PreReviewState(TypedDict):
    session_id: str
    parent_session_id: str | None
    request_id: str
    version: int
    normalized_request: dict
    parsed_requirement: dict
    retrieval_plan: dict
    retrieved_candidates: list
    evidence_pack: list
    capability_judgement: dict
    missing_info_items: list
    risk_items: list
    impact_items: list
    report: dict
    status: str
    error_message: str | None
```

状态值建议：

- `PROCESSING`
- `DONE`
- `FAILED`

---

## 4. 节点 I/O 契约

## 4.1 `InputNormalizer`

- 输入：`requirementText/backgroundText/additionalContext/attachments`
- 输出：`normalized_request`

## 4.2 `RequirementParser`

输出固定 schema：

```json
{
  "goal": "",
  "actors": [],
  "business_objects": [],
  "data_objects": [],
  "constraints": [],
  "expected_output": "",
  "uncertain_points": []
}
```

## 4.3 `RetrievalPlanner`

输出：

```json
{
  "queries": ["q1", "q2"],
  "source_filters": {},
  "module_tags": []
}
```

## 4.4 `KnowledgeRetriever`

- 输入：`retrieval_plan`
- 输出：`retrieved_candidates`（FTS + vector 合并结果）

## 4.5 `EvidenceSelector`

- 输入：`retrieved_candidates`
- 输出：`evidence_pack`（top8）

evidence item schema：

```json
{
  "doc_id": "",
  "doc_title": "",
  "chunk_id": "",
  "snippet": "",
  "source_type": "product_doc",
  "relevance_score": 0.0,
  "trust_level": "HIGH"
}
```

## 4.6 `CapabilityJudge`

输出：

```json
{
  "status": "SUPPORTED|PARTIALLY_SUPPORTED|NOT_SUPPORTED|NEED_MORE_INFO",
  "reason": "string",
  "confidence": "high|medium|low",
  "evidence_refs": ["chunk_id_1"]
}
```

规则：

1. 无高质量证据时禁止 `SUPPORTED`。
2. 高质量证据定义（M2）：`trust_level = HIGH` 且 `relevance_score >= 0.75`。
3. 至少有 1 条高质量证据，`status` 才允许为 `SUPPORTED`。

## 4.7 `MissingInfoAnalyzer`

输出：

```json
[
  {
    "type": "permission_boundary",
    "question": "string",
    "priority": "HIGH|MEDIUM|LOW"
  }
]
```

## 4.8 `RiskAnalyzer`

输出：

```json
[
  {
    "type": "security",
    "description": "string",
    "level": "HIGH|MEDIUM|LOW"
  }
]
```

## 4.9 `ImpactAnalyzer`

输出：

```json
[
  {
    "module": "string",
    "reason": "string"
  }
]
```

## 4.10 `ReportComposer`

输出报告固定 8 区块：

1. 需求摘要
2. 能力判断
3. 结构化草案
4. 依据（evidence）
5. 待补充信息
6. 风险提示
7. 影响范围
8. 建议下一步

## 4.11 `PersistenceNode`

职责：

- 写 session 最终状态
- 写 report
- 写 evidence_items
- 写错误信息（如失败）

---

## 5. ModelClient 契约

```python
class ModelClient:
    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> dict: ...
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    def rerank(self, query: str, candidates: list[str]) -> list[int]: ...
```

约束：

1. 节点禁止直接调用厂商 SDK。
2. 所有结构化生成都要传 schema。
3. 所有模型调用必须记录 latency/token/cost。

---

## 6. 错误与降级契约

错误码：

- `VALIDATION_ERROR`
- `FILE_UPLOAD_ERROR`
- `FILE_PARSE_ERROR`
- `WORKFLOW_ERROR`
- `MODEL_ERROR`
- `RETRIEVAL_ERROR`
- `PERSISTENCE_ERROR`

降级：

1. 检索为空：只能 `NEED_MORE_INFO` 或 `NOT_SUPPORTED`
2. `RiskAnalyzer` 失败：风险区块置空 + 记录错误
3. `ImpactAnalyzer` 失败：影响区块置空 + 记录错误
4. `ReportComposer` 失败：session 标记 `FAILED`
5. 不满足“高质量证据”门禁时：不得输出 `SUPPORTED`
