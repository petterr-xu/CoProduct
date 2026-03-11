# CoProduct 后端任务拆解清单（基于确定版技术方案）
> Version: v0.2.0
> Last Updated: 2026-03-11
> Status: Updated

## 1. 范围与原则

- 本清单仅基于 `docs/coproduct_backend_technical_design.md`
- 固定技术栈：FastAPI + LangGraph + SQLAlchemy + PostgreSQL + pgvector + S3
- 按 “M1 -> M2 -> M3” 分阶段推进，优先打通主链路

---

## 2. 模块任务总览

## 2.1 核心模块

1. `core`：配置、鉴权、日志、数据库连接
2. `models/repositories`：数据模型与数据访问层
3. `services`：会话、预审、持久化、文件、历史
4. `workflow`：LangGraph 状态与 11 节点
5. `rag`：切片、检索、重排、索引
6. `api`：5 个固定接口
7. `prompts/schemas`：提示词与结构化 schema

## 2.2 依赖关系（先后顺序）

1. `core` -> `models/repositories`
2. `models/repositories` -> `services`
3. `services` + `workflow/state` -> `workflow/nodes`
4. `workflow` + `services` -> `api`
5. `file/rag` 与主链路并行，但上线前必须完成最小可用

---

## 3. M1：主链路可跑通（第一优先级）

目标：`POST /api/prereview` 到 `GET /api/prereview/{session_id}` 可完整跑通并落库。

## 3.1 工程骨架

1. 创建 `backend/app` 目录结构（按技术方案第 15 节）
2. 建立 `main.py`、路由注册、全局异常处理
3. 建立 `Pydantic Settings` 配置体系

## 3.2 基础能力

1. API Token 鉴权中间件
2. JSON Lines 日志（request_id/session_id/node_name/latency/error_code）
3. SQLAlchemy 连接与会话管理

## 3.3 数据库与持久化

1. 建 `requests/sessions/reports/evidence_items` 四张核心表
2. 建 repository 接口与 SQLAlchemy 实现
3. 实现 `PersistenceService`（保存中间状态 + 报告 + 错误）

## 3.4 工作流骨架

1. 定义 `PreReviewState`
2. 构建 LangGraph 图（10 节点 + `PersistenceNode`）
3. 先实现节点占位逻辑，确保图可执行
4. 实现失败路径：任何节点异常可落 `WORKFLOW_ERROR`

## 3.5 API 最小可用

1. `POST /api/prereview`：创建 request/session，触发 workflow
2. `GET /api/prereview/{session_id}`：返回状态与报告结构

---

## 4. M2：结果质量可用（第二优先级）

目标：结果满足固定报告结构 + evidence 可追溯。

## 4.1 RAG 最小闭环

1. 知识表扩展：`knowledge_documents/knowledge_chunks`
2. 实现固定检索流程：
   - FTS top20
   - 向量 top20
   - 合并去重
   - rerank top8
3. `EvidenceSelector` 输出固定 evidence 结构

## 4.2 节点能力补全

1. `RequirementParser`：按固定 schema 输出
2. `CapabilityJudge`：强制枚举 + 无高质量证据不能 `SUPPORTED`
3. `CapabilityJudge`：输出 `confidence`（`high|medium|low`）
4. `MissingInfoAnalyzer/RiskAnalyzer/ImpactAnalyzer`：按默认检查项输出
5. `ReportComposer`：固定 8 区块 + evidence 引用

## 4.3 ModelClient 接入

1. 定义统一 `ModelClient` 接口
2. 节点改为只调用 `ModelClient`
3. 结构化输出全部绑定 schema

## 4.4 详情接口契约对齐（M2 必做）

1. `GET /api/prereview/{session_id}` 输出字段级 view model（不返回裸 `report`）
2. 状态枚举统一为 `PROCESSING|DONE|FAILED`（`NOT_FOUND` 仅错误体使用）
3. 固化 `capability.confidence` 字段并返回稳定值域
4. 实现 `SUPPORTED` 门禁：不满足高质量证据规则时强制降级

## 4.5 M2 完成定义（DoD）

1. 报告 8 区块可稳定输出且字段名冻结
2. evidence 引用可追溯到 `evidence_items`
3. `capability.status/confidence` 符合契约值域
4. 详情接口契约可被前端直接消费，无需二次猜测映射

---

## 5. M3：版本、文件、历史与稳定性（第三优先级）

目标：满足完整交付标准（第 17 节）。

> Obsolete in v0.2.0:
> 原 M3 拆解粒度偏粗，未体现当前代码与目标能力之间的差距（历史查询占位、附件仅上传未解析并入、节点降级策略未落地）。

### 5.0 [Obsolete] 原 M3 拆解（保留追溯）

1. regenerate 与版本链：`POST /api/prereview/{session_id}/regenerate`、`version +1`、`parent_session_id` 指向旧 session、重走 workflow
2. 文件链路：`uploaded_files` 表 + `POST /api/files/upload`、白名单和大小限制、解析并入 `normalized_request`
3. 历史查询：`GET /api/history` 分页 + `keyword/capabilityStatus/page/pageSize`
4. 稳定性与降级：固定错误码、空检索降级、Risk/Impact 降级、耗时与 token/cost 记录

## 5.1 [Updated v0.2.0] regenerate 与版本链

1. 保持现有契约：`POST /api/prereview/{session_id}/regenerate` 返回新 `sessionId`
2. 强化版本链校验：`version = old.version + 1`，`parent_session_id = old.session_id`
3. 约束 attachments 行为：regenerate 的 `attachments.fileId` 必须进入工作流输入并参与后续解析并入流程
4. 补齐失败分支：父 session 不存在、request 不存在、workflow 失败分别落明确错误码

## 5.2 [Updated v0.2.0] 文件链路（拆分实施）

### 5.2.1 上传与元数据（基线）

1. `POST /api/files/upload` 维持白名单/大小限制
2. 返回字段固定：`fileId/fileName/fileSize/parseStatus`
3. `uploaded_files` 落库完整（含 `mime_type/storage_key/parse_status`）

### 5.2.2 解析状态流转

1. 定义并落地 `parseStatus` 状态：`PENDING -> PARSING -> DONE|FAILED`
2. 解析失败时返回或记录 `FILE_PARSE_ERROR`，但不破坏上传元数据可追踪性
3. 支持最小可用格式解析（建议先 txt/md，再扩展 pdf/docx）

### 5.2.3 并入预审输入

1. 在 create/regenerate 中读取 `attachments.fileId` 对应解析文本
2. 将解析文本并入 `normalized_request.merged_text`
3. 对解析失败或缺失文件执行降级策略（记录告警并继续主流程，不直接中断）

## 5.3 [Updated v0.2.0] 历史查询（替换占位实现）

1. 用 repository 实现真实 `GET /api/history` 分页查询
2. 支持筛选：`keyword`、`capabilityStatus`
3. 返回稳定字段：`sessionId/requestText/capabilityStatus/version/createdAt`
4. 固化排序规则（默认按创建时间倒序）与分页边界（`page>=1`、`1<=pageSize<=100`）

## 5.4 [Updated v0.2.0] 稳定性与降级

1. 固化错误码分类：至少覆盖 `VALIDATION_ERROR/WORKFLOW_ERROR/PERSISTENCE_ERROR/FILE_UPLOAD_ERROR/FILE_PARSE_ERROR`
2. 检索空结果降级：仍返回可用报告（保守能力判断）
3. 节点降级策略：`RiskAnalyzer/ImpactAnalyzer` 异常时写空区块继续返回；`ReportComposer` 异常仍标记 `FAILED`
4. 日志与观测：补齐节点级耗时日志；保留模型级 latency/token/cost 日志

## 5.5 [Updated v0.2.0] M3 完成定义（DoD）

1. 历史查询不再是占位返回，真实分页与筛选可用
2. 附件从上传到解析到并入预审输入形成闭环
3. regenerate 支持版本链与附件输入联动
4. 风险/影响节点异常不阻断主流程（按降级策略返回）
5. 错误码与日志可支持联调和问题定位

---

## 6. 任务颗粒度建议（执行方式）

1. 每个节点单独一个任务卡，包含：
   - 输入字段
   - 输出字段
   - 失败行为
   - 测试样例
2. 每个 API 单独一个任务卡，包含：
   - 请求/响应 schema
   - 错误码
   - 鉴权与参数校验
3. 每个里程碑设置 “冻结点”，冻结后只修 bug，不加新功能。

---

## 7. 风险前置

1. 模型输出不稳定：先规则兜底，再调 prompt。
2. 检索质量不足：先保守结论（`NEED_MORE_INFO`/`NOT_SUPPORTED`）。
3. 文件解析质量波动：先支持少量稳定格式与大小。
4. 版本链混乱：先固化 session/version 规则再开发 regenerate。
