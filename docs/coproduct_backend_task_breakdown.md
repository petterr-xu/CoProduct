# CoProduct 后端任务拆解清单（基于确定版技术方案）

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
3. `MissingInfoAnalyzer/RiskAnalyzer/ImpactAnalyzer`：按默认检查项输出
4. `ReportComposer`：固定 8 区块 + evidence 引用

## 4.3 ModelClient 接入

1. 定义统一 `ModelClient` 接口
2. 节点改为只调用 `ModelClient`
3. 结构化输出全部绑定 schema

---

## 5. M3：版本、文件、历史与稳定性（第三优先级）

目标：满足完整交付标准（第 17 节）。

## 5.1 regenerate 与版本链

1. `POST /api/prereview/{session_id}/regenerate`
2. 新建 session：`version +1`、`parent_session_id` 指向旧 session
3. 重走完整 workflow

## 5.2 文件链路

1. `uploaded_files` 表 + `POST /api/files/upload`
2. 文件白名单和大小限制
3. 解析入口（txt/md/pdf/docx）并并入 `normalized_request`

## 5.3 历史查询

1. `GET /api/history` 分页
2. 支持 `keyword/capabilityStatus/page/pageSize`
3. 支持版本链返回

## 5.4 稳定性与降级

1. 实现固定错误码分类
2. 检索空结果降级
3. Risk/Impact 节点失败降级
4. 节点级耗时、模型耗时、token/cost 记录

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
