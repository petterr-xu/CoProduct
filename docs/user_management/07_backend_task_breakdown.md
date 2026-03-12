# 后端任务拆解文档 - user_management
> Version: v0.2.1
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

## 4. 依赖与执行顺序

### 4.1 依赖

1. BE-1.3 依赖 BE-1.1 + BE-1.2。
2. BE-1.4 依赖 BE-1.3。
3. BE-1.5 依赖 BE-1.4。
4. BE-2.x 依赖 Phase 1 全部稳定并完成前端联调。
5. BE-1.10（重放防护）依赖 BE-1.3（认证服务）与 BE-1.1（auth_sessions schema）。

### 4.2 推荐顺序

1. 先 schema 与迁移，再做认证服务。
2. 认证稳定后再切业务鉴权，避免主链路中断。
3. 管理员接口放 Phase 2，避免阻塞上线。

## 5. 风险与缓解

1. 风险：迁移上线后历史数据无归属导致查询缺失。
- 缓解：提供回填脚本与默认组织策略。
2. 风险：access/refresh 逻辑漏洞导致会话绕过。
- 缓解：会话表强校验 + refresh 轮换 + 吊销校验。
3. 风险：权限判定分散在多处造成不一致。
- 缓解：集中封装 `permission_guard`，禁止路由层手写条件。
4. 风险：保留旧 token 兼容窗口带来安全风险。
- 缓解：仅 dev 环境允许，生产禁用并做启动检查。
