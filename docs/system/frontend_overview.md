Title: Frontend Overview
Version: v1.0.0
Last Updated: 2026-03-13
Scope: frontend/src 当前页面结构、状态管理与 API 协同
Audience: Frontend developers, full-stack developers, reviewers

# Frontend Overview

## Responsibilities and Boundaries

前端负责：

1. 登录、会话恢复、路由守卫、权限可见性控制。
2. 预审发起、详情展示、再生成、历史检索等交互。
3. 管理后台页面（成员、职能、API key、审计）与请求编排。
4. 错误文案映射和用户可读反馈。

前端不负责：

1. 权限规则最终裁决（后端为准）。
2. 报告计算与检索逻辑。
3. 业务数据持久化。

## Structure and Layering

目录分层（`frontend/src`）：

1. `app/`
- App Router 路由入口。
- 页面级容器与 route redirect。
2. `components/`
- `auth/base/layout/business` 通用组件。
3. `features/`
- 页面级业务模块（create-review、review-detail、admin 等）。
4. `hooks/`
- React Query hooks，封装数据获取和 mutation。
5. `lib/`
- `auth-client`、`api-client`、`http-client`、常量与工具。
6. `stores/`
- Zustand 登录态与局部状态。
7. `types/`
- 前端契约类型定义。

## Runtime Flow and Error Paths

### Flow A: App Bootstrap and Guard

1. `Providers` 初始化 React Query 与 `AuthBootstrap`。
2. `AuthBootstrap` 流程：
- 有 access token：`/auth/me -> /auth/context`。
- 无 access token：`/auth/refresh -> /auth/me -> /auth/context`。
3. `RouteGuard` 根据 `hasBootstrapped + user` 决定页面跳转。

### Flow B: API Call and Retry

1. 业务请求经 `api-client` 发出，自动附带 Bearer token。
2. 若遇 401，客户端会触发一次 refresh 再重试原请求。
3. 仍失败则清理会话并跳回登录。

### Flow C: Admin Member Search for API Key Issue

1. API key 签发表单先确定组织上下文。
2. 通过 `/api/admin/member-options` 做前缀联想检索。
3. 选中成员后提交签发请求，成功后仅一次展示明文 key。

错误路径：

1. `ApiClientError` 统一承载 `httpStatus/code/status`。
2. `getApiErrorMessage` 按错误码映射用户可读文案。
3. 页面级组件统一处理 `loading/error/empty`。

## External Interfaces

前端调用接口分类：

1. `auth-client.ts`
- `/api/auth/key-login`
- `/api/auth/refresh`
- `/api/auth/logout`
- `/api/auth/me`
- `/api/auth/context`
2. `api-client.ts`
- 预审接口：`/api/prereview*`, `/api/history`, `/api/files/upload`
- 管理接口：`/api/admin/*`

## Configuration

| Key | Purpose | Example |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | 后端 API base URL | `http://localhost:8000` |

运行依赖：

1. Node.js >= 18.18（推荐 Node 20）。
2. Next.js 15 + React 19。

## Observability and Troubleshooting

1. 请求失败诊断
- 浏览器 Network + 后端日志联合排查。
- 通过错误码快速定位（如 `PERMISSION_DENIED`, `TOKEN_EXPIRED`）。
2. 会话诊断
- 刷新后若回登录页，优先检查 cookies 是否写入、域名是否统一（`localhost`）。
3. CORS 诊断
- 检查后端 `COPRODUCT_CORS_ALLOW_ORIGINS` 是否包含前端 origin。

## Known Risks and Next Improvements

1. 交互复杂度
- 管理页表单逻辑增长快，可考虑引入更细粒度 form/model 层。
2. 自动化测试
- 当前主要依赖 `typecheck + lint + 手工联调`，缺 E2E 回归。
3. 多组织体验
- `USER_SCOPED` 模式 UI 未开放，组织切换路径仍待实现。
