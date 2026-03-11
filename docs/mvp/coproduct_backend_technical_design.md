# CoProduct 后端技术设计方案（确定版）

> 适用范围：CoProduct 一期 / MVP  
> 目标：以单体后端承载 API、持久化、文件传输与核心 AI 工作流，输出一个可落地、可调试、可持续演进的后端系统。  
> 本方案是唯一落地方案，不是备选集合。

## 1. 方案结论

CoProduct 后端固定采用：

- 语言：Python 3.12
- Web 框架：FastAPI
- AI 工作流：LangGraph
- ORM：SQLAlchemy 2.x
- 数据库：PostgreSQL 16
- 向量检索：pgvector
- 全文检索：PostgreSQL Full Text Search
- 文件存储：S3 兼容对象存储
- 模型调用：统一 `ModelClient`
- 部署形态：单体服务
- 配置：Pydantic Settings
- 鉴权：一期单用户模式，固定 API Token
- 版本策略：regenerate 创建新 session，新 report version +1

AI 工作流层是后端中的核心业务子系统，不拆为独立服务。

## 2. 后端职责边界

后端承担：

- 提供 HTTP API
- 校验请求
- 管理预审会话
- 保存输入、输出、证据、历史
- 管理文件上传与引用
- 调度 AI 工作流
- 返回稳定结构化结果

一期不实现：

- 微服务拆分
- 多 Agent 自由协商
- 复杂任务队列
- 复杂权限 RBAC
- 外部系统深度集成
- 完整 MCP Server

## 3. 总体架构

```text
[Frontend]
   ↓ HTTP
[FastAPI App]
   ├── API Router
   ├── Auth Middleware
   ├── Request Validation
   ├── Session Service
   ├── File Service
   ├── History Service
   ├── Persistence Service
   └── PreReview Service
          ↓
      [LangGraph Workflow]
          ├── InputNormalizer
          ├── RequirementParser
          ├── RetrievalPlanner
          ├── KnowledgeRetriever
          ├── EvidenceSelector
          ├── CapabilityJudge
          ├── MissingInfoAnalyzer
          ├── RiskAnalyzer
          ├── ImpactAnalyzer
          ├── ReportComposer
          └── PersistenceNode
                ↓
      [PostgreSQL + pgvector + File Storage]
```

## 4. 核心设计原则

- 单体优先
- Workflow Agent 优先
- Evidence-first
- 结构化输出优先
- 结果可追踪

每次请求都必须能回看：

- 原始输入
- 中间解析
- 检索结果
- 最终证据
- 最终报告
- 版本关系

## 5. 模块设计

### 5.1 应用后端层模块

#### API Router
固定提供 5 个 API：

- `POST /api/prereview`
- `GET /api/prereview/{session_id}`
- `POST /api/prereview/{session_id}/regenerate`
- `GET /api/history`
- `POST /api/files/upload`

#### Session Service
职责：
- 创建 session
- 管理状态
- 维护 parent-child 关系
- 提供 version 信息

#### File Service
职责：
- 接收上传
- 保存对象存储
- 返回 `file_id`
- 记录文件元信息
- 触发文件解析入口

#### History Service
职责：
- 查询历史列表
- 查询详情
- 返回版本链

#### Persistence Service
职责：
- 保存 request / session / report / evidence
- 保存 workflow 中间结果
- 保存错误信息

#### PreReview Service
职责：
- 作为 API 与 AI 工作流之间的统一入口
- 创建任务上下文
- 调用 LangGraph
- 处理流程成功与失败

### 5.2 AI 工作流层模块

固定拆成 10 个节点：

1. `InputNormalizer`
2. `RequirementParser`
3. `RetrievalPlanner`
4. `KnowledgeRetriever`
5. `EvidenceSelector`
6. `CapabilityJudge`
7. `MissingInfoAnalyzer`
8. `RiskAnalyzer`
9. `ImpactAnalyzer`
10. `ReportComposer`

另加 `PersistenceNode`。

## 6. 工作流详细设计

### 6.1 状态对象

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

### 6.2 节点职责

#### 1）InputNormalizer
- 清理文本
- 合并补充信息
- 截断超长内容
- 生成统一输入对象

#### 2）RequirementParser
固定输出：

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

规则：
- 必须结构化输出
- 字段缺失时补空数组或空字符串

#### 3）RetrievalPlanner
输出：
- 2~5 个 query
- source filters
- module tags

#### 4）KnowledgeRetriever
固定策略：
- PostgreSQL 全文召回
- pgvector 向量召回
- 合并去重
- 返回前 N 条候选证据

#### 5）EvidenceSelector
- rerank
- 去掉弱相关片段
- 聚合同文档相邻片段
- 形成最终 `evidence_pack`

#### 6）CapabilityJudge
固定结论枚举：

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `NOT_SUPPORTED`
- `NEED_MORE_INFO`

规则：
- 无高质量证据时不能输出 `SUPPORTED`

#### 7）MissingInfoAnalyzer
默认检查：
- 目标用户
- 数据范围
- 触发条件
- 输出形式
- 权限边界
- 时间要求
- 性能要求

#### 8）RiskAnalyzer
默认检查：
- 权限与安全
- 数据一致性
- 边界条件
- 兼容性
- 实施复杂度
- 依赖模块

#### 9）ImpactAnalyzer
一期固定通过：
- 模块标签命中
- 文档标签命中
- 简单规则表

#### 10）ReportComposer
组装标准报告结构并附带证据引用。

## 7. RAG 设计

### 7.1 一期知识源固定范围

只接入：

1. 产品能力说明
2. 模块说明文档
3. API 文档
4. 常见限制说明
5. 少量高质量历史需求案例

### 7.2 文档切片规则

- 按标题层级 + 段落切片
- 每片约 500~800 中文字符
- 相邻切片重叠 80~120 字
- 保留文档标题、章节路径、更新时间、source_type、trust_level

### 7.3 检索规则

固定流程：

1. RequirementParser 产出关键词
2. RetrievalPlanner 生成 query
3. 全文检索 top 20
4. 向量检索 top 20
5. 合并去重
6. EvidenceSelector rerank 到 top 8

### 7.4 evidence 结构

```json
[
  {
    "doc_id": "",
    "doc_title": "",
    "chunk_id": "",
    "snippet": "",
    "source_type": "product_doc",
    "relevance_score": 0.0,
    "trust_level": "HIGH"
  }
]
```

## 8. 数据库设计

固定表：

### `requests`
- `id`
- `requirement_text`
- `background_text`
- `business_domain`
- `module_hint`
- `created_at`

### `sessions`
- `id`
- `request_id`
- `parent_session_id`
- `version`
- `status`
- `started_at`
- `finished_at`
- `error_message`

### `reports`
- `id`
- `session_id`
- `summary`
- `capability_status`
- `report_json`
- `created_at`

### `evidence_items`
- `id`
- `session_id`
- `doc_id`
- `chunk_id`
- `doc_title`
- `snippet`
- `relevance_score`
- `source_type`
- `trust_level`

### `knowledge_documents`
- `id`
- `title`
- `source_type`
- `trust_level`
- `file_id`
- `metadata_json`
- `updated_at`

### `knowledge_chunks`
- `id`
- `doc_id`
- `chunk_text`
- `section_path`
- `embedding`
- `tsv`

### `uploaded_files`
- `id`
- `file_name`
- `file_size`
- `mime_type`
- `storage_key`
- `parse_status`
- `created_at`

## 9. API 设计

### `POST /api/prereview`
请求体：

```json
{
  "requirementText": "",
  "backgroundText": "",
  "businessDomain": "",
  "moduleHint": "",
  "attachments": [{"fileId": ""}]
}
```

返回：

```json
{
  "sessionId": "",
  "status": "PROCESSING"
}
```

### `GET /api/prereview/{session_id}`
返回状态与完整报告。

### `POST /api/prereview/{session_id}/regenerate`
请求体：

```json
{
  "additionalContext": "",
  "attachments": [{"fileId": ""}]
}
```

行为：
- 基于旧 session 创建新 session
- version +1
- 重走完整 workflow

### `GET /api/history`
支持：
- `keyword`
- `capabilityStatus`
- `page`
- `pageSize`

### `POST /api/files/upload`
行为：
- 上传对象存储
- 写 `uploaded_files`
- 返回 `file_id`

## 10. 文件处理设计

固定两段：

### 第一步：上传
- 前端上传原始文件
- 后端写入对象存储
- 返回 `file_id`

### 第二步：解析
- 在创建预审或 regenerate 时读取文件
- 执行文本抽取
- 将抽取结果并入 `normalized_request`

一期只支持：
- txt
- md
- pdf
- docx

## 11. Model Client 设计

统一实现：

```python
class ModelClient:
    def structured_invoke(self, prompt_name: str, input_data: dict, schema: type) -> dict: ...
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    def rerank(self, query: str, candidates: list[str]) -> list[int]: ...
```

规则：

- 所有模型调用都通过 `ModelClient`
- 不允许节点直接调用第三方 SDK
- 所有结构化输出必须绑定 schema

## 12. Prompt 与 Schema 管理

固定目录：

```text
backend/
  prompts/
    requirement_parser.md
    retrieval_planner.md
    capability_judge.md
    missing_info_analyzer.md
    risk_analyzer.md
    impact_analyzer.md
    report_composer.md
  schemas/
    requirement.py
    retrieval.py
    report.py
    evidence.py
```

## 13. 错误处理与降级

固定错误分类：

- `VALIDATION_ERROR`
- `FILE_UPLOAD_ERROR`
- `FILE_PARSE_ERROR`
- `WORKFLOW_ERROR`
- `MODEL_ERROR`
- `RETRIEVAL_ERROR`
- `PERSISTENCE_ERROR`

降级规则：

- 检索为空：允许继续，但能力判断只能为 `NEED_MORE_INFO` 或 `NOT_SUPPORTED`
- RiskAnalyzer 失败：风险区块置空并记录 error
- ImpactAnalyzer 失败：影响范围区块置空并记录 error
- ReportComposer 失败：session 失败

## 14. 日志与可观测性

固定记录：

- request_id
- session_id
- workflow node name
- node latency
- model call latency
- final status
- error code
- total tokens
- total cost（如可获取）

日志采用 JSON Lines。

## 15. 目录结构（确定版）

```text
backend/
  app/
    main.py
    api/
      prereview.py
      history.py
      files.py
    core/
      config.py
      auth.py
      logging.py
      db.py
    models/
    repositories/
    services/
      prereview_service.py
      history_service.py
      file_service.py
      persistence_service.py
    workflow/
      graph.py
      state.py
      nodes/
        input_normalizer.py
        requirement_parser.py
        retrieval_planner.py
        knowledge_retriever.py
        evidence_selector.py
        capability_judge.py
        missing_info_analyzer.py
        risk_analyzer.py
        impact_analyzer.py
        report_composer.py
        persistence_node.py
    rag/
      chunking.py
      indexer.py
      search.py
      rerank.py
    prompts/
    schemas/
    utils/
```

## 16. 安全设计

一期只做最小安全能力：

- API Token 鉴权
- 文件类型白名单
- 文件大小限制
- SQL 参数化
- 不信任前端传入的 file_id 与 session_id
- 不返回内部堆栈

## 17. 交付标准

后端完成判定标准：

1. `POST /api/prereview` 可创建任务
2. 工作流可跑通 10~20 条典型样例
3. `GET /api/prereview/{id}` 可查询状态与结果
4. 结果包含固定 8 个报告区块
5. evidence 可追溯到文档与 chunk
6. regenerate 可生成新版本
7. 历史列表可分页查询
8. 文件上传可返回稳定 `file_id`
9. 工作流失败时可定位到节点
10. 所有数据可在 PostgreSQL 中回查

## 18. 最终结论

CoProduct 后端的唯一实现目标是：  
**用一个单体 FastAPI 服务，把 API、数据、文件与 AI 工作流稳定收口。**

因此，本方案固定为：

- **FastAPI 作为系统入口**
- **LangGraph 作为 AI 工作流核心**
- **PostgreSQL + pgvector 作为统一数据底座**
- **S3 兼容对象存储作为文件承载**
- **结构化输出 + Evidence-first 作为结果生成原则**
