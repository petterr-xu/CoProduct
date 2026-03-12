Title: Backend Overview
Version: v1.0.0
Last Updated: 2026-03-13
Scope: backend/app 当前实现、分层职责、接口与运行行为
Audience: Backend developers, reviewers, SRE collaborators

# Backend Overview

## Responsibilities and Boundaries

后端负责：

1. 提供统一 HTTP API（认证、预审、历史、文件、管理）。
2. 执行预审工作流并持久化结果。
3. 管理组织身份、权限规则、API key 和审计日志。
4. 实现检索支撑能力（内置知识 + 混合检索）。

后端不负责：

1. 前端路由与页面状态管理。
2. 外部云模型或外部知识平台接入（当前未实现）。
3. 复杂异步任务编排（当前无独立任务队列）。

## Structure and Layering

目录分层（`backend/app`）：

1. `api/`
- FastAPI routers。
- 入参模型与 HTTP 错误映射。
2. `core/`
- 配置、DB、鉴权依赖、权限校验、安全工具、日志。
3. `services/`
- 业务用例编排与治理规则核心。
4. `repositories/`
- SQLAlchemy 查询和写入。
5. `workflow/`
- LangGraph 图与节点。
6. `rag/`
- 混合检索与内置知识初始化。
7. `models/`
- 业务与治理数据模型。
8. `model_client/`
- 模型能力抽象与当前 heuristic 实现。

## Runtime Flow and Error Paths

### Flow A: Startup

1. 校验安全配置（生产模式禁止不安全配置）。
2. `Base.metadata.create_all` 创建缺失表。
3. 执行 `ensure_runtime_schema_compatibility` 补齐旧库缺列。
4. `AuthService.ensure_bootstrap_identity` 确保 bootstrap owner + key。
5. 回填默认职能角色并初始化内置知识文档。

### Flow B: PreReview Request

1. API 层校验写权限。
2. Service 创建 request/session 并构造初始 state。
3. Workflow 节点串行执行，返回 final_state。
4. PersistenceService 持久化报告、证据、状态。
5. 若异常，session 标记为 `FAILED` 并带 `error_message`。

### Flow C: Auth Refresh

1. API 层提取 cookies 和 `X-CSRF-Token`。
2. AuthService 校验 refresh JWT、CSRF、session hash/version。
3. 成功则轮换 refresh token 并返回新 access token。

错误路径设计：

1. 领域错误通过 `AuthServiceError/AdminServiceError` 带 `error_code + http_status`。
2. API 层将异常映射为统一 `detail` 结构。
3. 预审链路默认错误码为 `WORKFLOW_ERROR`，治理链路按规则返回细分错误码。

## External Interfaces

主要 API 组：

1. Health
- `GET /healthz`
2. Auth
- `POST /api/auth/key-login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/context`
3. PreReview
- `POST /api/prereview`
- `GET /api/prereview/{session_id}`
- `POST /api/prereview/{session_id}/regenerate`
- `GET /api/history`
- `POST /api/files/upload`
4. Admin
- `GET/POST/PATCH /api/admin/users...`
- `GET/PATCH /api/admin/members...`
- `GET/POST/PATCH /api/admin/functional-roles...`
- `GET/POST/POST /api/admin/api-keys...`
- `GET /api/admin/member-options`
- `GET /api/admin/audit-logs`

## Configuration

核心配置来自 `COPRODUCT_*` 环境变量（`core/config.py`）：

| Key | Purpose | Default |
|---|---|---|
| `COPRODUCT_AUTH_MODE` | 鉴权模式 (`jwt/hybrid/legacy`) | `jwt` |
| `COPRODUCT_DATABASE_URL` | SQLAlchemy 连接串 | PostgreSQL local |
| `COPRODUCT_JWT_SECRET` | access JWT 签名密钥 | dev 值 |
| `COPRODUCT_REFRESH_TOKEN_SECRET` | refresh JWT 签名密钥 | dev 值 |
| `COPRODUCT_CSRF_SECRET` | CSRF 相关密钥预留 | dev 值 |
| `COPRODUCT_API_KEY_PEPPER` | API key hash pepper | dev 值 |
| `COPRODUCT_BOOTSTRAP_OWNER_API_KEY` | 首个 owner 登录密钥 | dev 值 |
| `COPRODUCT_UPLOAD_DIR` | 文件上传目录 | `./uploaded_files` |
| `COPRODUCT_CORS_ALLOW_ORIGINS` | CORS 白名单 | `http://localhost:3000` |

## Observability and Troubleshooting

1. Logging
- `log_event` 输出 JSON 日志，包含 `ts/event/...`。
- 节点级日志包含 `node_completed`、`node_degraded`。
2. 常见排障入口
- 认证问题：`AUTH_LOGIN/AUTH_REFRESH/AUTH_LOGOUT` 审计与日志。
- 预审问题：`workflow_failed`、`node_degraded`、session `error_message`。
- 管理问题：`audit_logs` 的 `FAILED` 记录。

## Known Risks and Next Improvements

1. 迁移体系
- 当前依赖 runtime patch，不适合长期版本演进。
2. 模型能力
- Heuristic 客户端无法保证复杂语义质量。
3. 性能
- 串行节点在负载上升时延迟增加，缺并行与任务队列。
4. 观测
- 缺 metrics/trace 体系，线上诊断依赖日志经验。
