Title: System Overview
Version: v1.0.0
Last Updated: 2026-03-13
Scope: CoProduct 当前系统目标、边界、能力与术语
Audience: Product engineers, backend/frontend developers, reviewers

# System Overview

## Background and Goals

CoProduct 是一个“需求预审 + 组织治理”系统，目标是：

1. 让业务成员可以快速提交需求并获得结构化预审结果。
2. 让组织管理员可以管理成员身份、权限、职能角色、API Key 与审计记录。
3. 在本地可复现环境中，提供稳定可演进的 Agent 编排骨架（LangGraph + deterministic model client）。

当前实现重点是工程闭环与可维护性，而非最强模型能力。

## System Boundary

系统当前覆盖：

1. 认证与会话：API Key 登录、JWT access token、refresh cookie + CSRF。
2. 预审业务：创建预审、查询详情、再生成、历史列表、附件上传。
3. 组织治理：成员管理、职能角色管理、API Key 管理、审计日志查询。
4. 检索支撑：内置知识文档初始化、混合检索（词法 + 向量）与证据重排。

系统当前不覆盖：

1. 用户自助注册/邀请激活完整流程。
2. 多组织主动切换 UI（`scopeMode=USER_SCOPED` 仅预留）。
3. 生产级云模型与外部知识源接入。
4. 标准化数据库迁移工具链（当前为运行时兼容补丁）。

## Capability Map

| Capability | Entry | Core Backend | Persistence |
|---|---|---|---|
| Auth Session | `/login` | `AuthService` + `auth.py` | `users/memberships/api_keys/auth_sessions/audit_logs` |
| PreReview Run | `/prereview/new` | `PreReviewService` + `PreReviewWorkflow` | `requests/sessions/reports/evidence_items` |
| History Query | `/history` | `HistoryService` | `sessions + reports + requests` |
| File Upload | create/regenerate form | `FileService` + `AttachmentService` | `uploaded_files + local uploaded_files/` |
| Admin Governance | `/admin/*` | `AdminUserService` | user-management tables + `audit_logs` |
| Retrieval Support | workflow internal | `HybridSearcher` + node chain | `knowledge_documents/knowledge_chunks` |

## End-to-End User Journeys

### Journey A: API Key Login and Session Bootstrap

1. 用户在 `/login` 输入 API Key。
2. 前端调用 `POST /api/auth/key-login`，后端验证哈希后签发 access token，并设置 refresh/csrf cookies。
3. 前端保存 access token 到 Zustand，后续请求走 `Authorization: Bearer <token>`。
4. 页面刷新时，`AuthBootstrap` 自动尝试 `POST /api/auth/refresh` 恢复会话。

### Journey B: Create and Read PreReview

1. 用户在 `/prereview/new` 填写需求并可上传附件。
2. 前端先上传附件拿到 `fileId`，再调用 `POST /api/prereview` 发起预审。
3. 后端创建 request/session，执行 LangGraph 工作流并持久化报告。
4. 前端进入详情页并按状态轮询 `GET /api/prereview/{sessionId}`。

### Journey C: Admin Governance

1. 管理员访问 `/admin/users`、`/admin/functional-roles`、`/admin/api-keys`、`/admin/audit-logs`。
2. 后端统一要求 `OWNER/ADMIN` 角色，并在 service 层执行治理规则。
3. 对成员状态、角色、API Key 的关键操作会写入审计日志。

## Current Capabilities and Limitations

当前可用能力：

1. 前后端联调闭环稳定，具备可用登录态恢复和权限隔离。
2. 预审工作流具备结构化中间产物和最终报告映射。
3. 成员治理具备关键保护策略：自操作保护、OWNER 底线、ADMIN 边界。
4. API Key 管理支持“吊销 key 联动失效相关会话”。

当前主要限制：

1. 模型与检索质量受 `HeuristicModelClient` 限制，偏向可复现而非智能上限。
2. 工作流为串行执行，无并行子图与细粒度超时重试。
3. `create_all + schema_compat` 不等同于正式 migration 策略。
4. 可观测以结构化日志为主，缺统一 metrics/trace 面板。

## Glossary

| Term | Meaning |
|---|---|
| PreReview | 一次需求预审任务，从创建到报告输出的完整链路 |
| Request | 原始需求输入实体（`requests` 表） |
| Session | 预审执行实例，支持版本与再生成（`sessions` 表） |
| Report | 结构化预审结果快照（`reports.report_json`） |
| Membership | 用户在组织内的身份（权限角色 + 成员状态 + 职能角色） |
| Functional Role | 组织内职能角色，如产品、运营（`org_function_roles`） |
| Access Token | 短期 JWT，用于 API 鉴权 |
| Refresh Session | 持久会话，用 refresh cookie 轮换 access token |
| CSRF Token | 防跨站请求伪造的双提交 token（header + cookie） |
| Hybrid Search | 词法召回 + 向量召回 + 合并重排的检索策略 |
