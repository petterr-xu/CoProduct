# 后端任务拆解文档 - user_management
> Version: v0.4.0
> Last Updated: 2026-03-12
> Status: Draft

## 1. Phase 1 任务

目标：建立可用用户认证体系并接管业务鉴权。

1. BE-1.1 数据模型与迁移
- 新增表：`organizations/users/memberships/api_keys/auth_sessions/audit_logs`。
- 为 `requests/sessions/uploaded_files` 增加 `org_id/created_by_user_id`。
2. BE-1.2 安全组件
- JWT 签发与验证。
- API Key 哈希工具与生成工具。
3. BE-1.3 认证服务
- `key-login/refresh/logout/me` 服务实现。
- 会话创建、轮换与失效。
> Obsolete in v0.2.0: refresh/logout 的 body token 解析路径不再作为主实现。
4. BE-1.3a Cookie + CSRF 刷新链路（v0.2.0）
- `refresh/logout` 改为基于 `refresh_token` cookie + `X-CSRF-Token`。
- 登录/刷新时轮换并下发 cookie。
5. BE-1.4 鉴权依赖替换
- `verify_api_token` -> `get_current_user`。
- 业务路由统一接入新依赖。
6. BE-1.5 业务数据归属
- 创建请求/会话/文件时写入用户与组织归属。
- 查询接口默认加组织与用户过滤。
7. BE-1.6 审计日志（基础）
- 登录、刷新、登出记录。
8. BE-1.7 权限矩阵落地（v0.2.0）
- 固化 `OWNER/ADMIN/MEMBER/VIEWER` 端点级权限规则。
- 固化 `MEMBER` 仅本人数据规则与 `VIEWER` 只读规则。
9. BE-1.8 鉴权模式开关与环境守卫（v0.2.1）
- 新增 `COPRODUCT_AUTH_MODE=legacy|hybrid|jwt`。
- 生产环境启动校验（禁用 legacy/hybrid、禁用 `dev-token`、密钥必填）。
10. BE-1.9 历史数据归属回填（v0.2.1）
- 完成 `org_id/created_by_user_id` 回填脚本与一致性校验 SQL。
11. BE-1.10 Refresh 重放防护（v0.2.1）
- session 轮换 one-time token 策略。
- 同步并发刷新控制（行级锁或乐观锁）。

## 2. Phase 2 任务

目标：提供团队治理能力。

1. BE-2.1 管理员接口
- 用户创建、禁用、角色变更。
2. BE-2.2 API Key 生命周期
- 签发、查询、吊销。
3. BE-2.3 权限策略中间层
- `OWNER/ADMIN/MEMBER/VIEWER` 权限判断。
4. BE-2.4 审计日志查询接口
- 支持分页、按 actor/action 过滤。
5. BE-2.5 测试补齐
- 认证集成测试、权限边界测试、回归测试。
6. BE-2.6 管理列表接口标准化（v0.2.0）
- `GET /api/admin/users` 与 `GET /api/admin/api-keys` 返回统一分页结构。
- 查询参数统一分页/筛选口径。
7. BE-2.7 鉴权可观测与告警（v0.2.1）
- 增加登录/刷新/重放拦截指标与告警阈值。
- 增加 `auth_legacy_fallback_total`，支撑灰度期观测。

## 3. Phase 3..N 任务

目标：安全增强与企业集成预留。

1. BE-3.1 邀请制注册与激活流程。
2. BE-3.2 限流与风险控制（登录失败阈值、IP 限制）。
3. BE-3.3 会话安全增强（异常登录检测、批量下线）。
4. BE-3.4 OIDC 抽象层（接口预留）。

## 3A. Phase 4 任务（v0.3.0 新增）

目标：细化身份域建模、明确 OWNER/ADMIN 边界、落地治理红线与职能角色。

1. BE-4.1 身份模型分层重构
- 明确全局身份（`users`）与组织成员身份（`memberships`）职责边界。
- 新增或重构状态字段：`account_status` 与 `member_status`。
2. BE-4.2 职能角色数据模型
- 新增 `org_function_roles` 表。
- `memberships` 新增 `functional_role_id`，约束单成员单职能。
3. BE-4.3 权限边界差异化
- 落地 OWNER/ADMIN 的差异规则（admin 不可操作 owner）。
- 服务层集中封装权限判断，禁止路由层分散实现。
4. BE-4.4 治理红线约束
- 至少一个 active owner 约束。
- 禁止危险自操作（自降权/自禁用）。
- 禁用成员联动失效 sessions 与 API keys。
5. BE-4.5 成员语义 API 演进
- 新增 `/api/admin/members/*` 与 `/api/admin/functional-roles/*`。
- 保留 `/api/admin/users/*` 兼容层并提供迁移计划。
6. BE-4.6 审计与错误码增强
- 高风险拒绝操作必须写 `FAILED` 审计并带 `reason`。
- 新增治理类错误码（如 `LAST_OWNER_PROTECTED`）。
7. BE-4.7 迁移与回填
- 为组织初始化默认职能 `unassigned` 并回填历史 membership。
- 输出一致性校验 SQL 与回滚脚本。
8. BE-4.8 测试补齐
- owner 红线测试、admin 操作 owner 拒绝测试、职能跨组织绑定测试。

## 3B. Phase 5 任务（v0.4.0 新增）

目标：统一登录上下文契约，收敛创建成员组织语义，支撑前端组织下拉与未来多组织登录扩展。

1. BE-5.1 新增登录上下文接口（关联 TD-401 / BC-401）
- 在 `GET /api/auth/context` 返回 `user/activeOrg/availableOrgs/scopeMode`。
- 复用现有认证依赖，确保响应字段与前端契约一致。
2. BE-5.2 创建成员组织约束收敛（关联 TD-402/TD-403 / BC-402）
- `POST /api/admin/users` 将 `orgId` 标记为兼容字段。
- 强制 `orgId`（若传入）必须等于 `current_user.org_id`。
3. BE-5.3 无组织场景错误码（关联 TD-403 / BC-403）
- 当当前用户无有效组织上下文时，返回 `NO_ACTIVE_ORG`。
- 写入 `FAILED` 审计日志并记录原因。
4. BE-5.4 上下文作用域预留（关联 TD-404 / BC-401）
- 增加 `scopeMode` 生成逻辑，当前固定 `ORG_SCOPED`。
- 预留 `USER_SCOPED` 分支扩展点，不影响现有 API Key 登录。
5. BE-5.5 自动化测试补齐（关联 TD-401~TD-404）
- 覆盖 context 接口、跨组织创建拒绝、无组织错误码、scopeMode 响应。

## 4. 依赖与执行顺序

### 4.1 依赖

1. BE-1.3 依赖 BE-1.1 + BE-1.2。
2. BE-1.4 依赖 BE-1.3。
3. BE-1.5 依赖 BE-1.4。
4. BE-2.x 依赖 Phase 1 全部稳定并完成前端联调。
5. BE-1.10（重放防护）依赖 BE-1.3（认证服务）与 BE-1.1（auth_sessions schema）。
6. BE-4.x 依赖 BE-2.x 管理能力稳定后开展。
7. BE-5.x 依赖 BE-4.x 成员与组织模型稳定；并被 FE-5.x 直接消费。

### 4.2 推荐顺序

1. 先 schema 与迁移，再做认证服务。
2. 认证稳定后再切业务鉴权，避免主链路中断。
3. 管理员接口放 Phase 2，避免阻塞上线。
4. Phase 4 先做 schema 与策略，再做接口演进与兼容层。
5. Phase 5 先出 `auth/context` 契约与实现，再收敛创建成员组织规则，最后补齐回归测试。

## 5. 风险与缓解

1. 风险：迁移上线后历史数据无归属导致查询缺失。
- 缓解：提供回填脚本与默认组织策略。
2. 风险：access/refresh 逻辑漏洞导致会话绕过。
- 缓解：会话表强校验 + refresh 轮换 + 吊销校验。
3. 风险：权限判定分散在多处造成不一致。
- 缓解：集中封装 `permission_guard`，禁止路由层手写条件。
4. 风险：保留旧 token 兼容窗口带来安全风险。
- 缓解：仅 dev 环境允许，生产禁用并做启动检查。
5. 风险：身份模型改造引入数据迁移不一致。
- 缓解：三步迁移（加字段->回填->加约束）并附一致性校验。
6. 风险：`auth/me` 与 `auth/context` 信息口径不一致。
- 缓解：定义 `auth/context` 为组织上下文唯一事实来源，并在契约中固定字段语义。

## 6. 追踪映射（v0.4.0 增量）

| BE 任务 | 关联 TD | 关联契约 |
|---|---|---|
| BE-5.1 | TD-401 | BC-401 |
| BE-5.2 | TD-402/TD-403 | BC-402 |
| BE-5.3 | TD-403 | BC-403 |
| BE-5.4 | TD-404 | BC-401 |
| BE-5.5 | TD-401~TD-404 | BC-401/BC-402/BC-403 |
