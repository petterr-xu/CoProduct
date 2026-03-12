# 后端检查清单 - user_management
> Version: v0.5.0
> Last Updated: 2026-03-12
> Status: Draft

## 1. 功能检查

### 1.1 Phase 1 功能

1. `POST /api/auth/key-login` 可签发 access/refresh token。
2. `POST /api/auth/refresh` 可轮换 token 并更新会话。
3. `POST /api/auth/logout` 可使会话失效。
4. `GET /api/auth/me` 返回当前用户信息。
5. 既有业务接口已接入 `get_current_user`。
6. 新建预审/文件时写入 `org_id/created_by_user_id`。
7. `refresh/logout` 采用 Cookie + `X-CSRF-Token` 校验流程，body token 路径已禁用。
8. `COPRODUCT_AUTH_MODE` 支持 `legacy|hybrid|jwt`，且 prod 环境禁止 `legacy/hybrid`。

### 1.2 Phase 2 功能

1. 管理员接口可创建/禁用用户、变更角色。
2. 可签发/查询/吊销 API Key。
3. 审计日志可查询关键操作记录。
4. 用户/API Key 列表接口返回统一分页结构（`items/total/page/pageSize`）。

### 1.3 Phase 4 功能（v0.3.0 新增）

1. `OWNER` 与 `ADMIN` 权限边界按新矩阵生效（admin 不能操作 owner）。
2. 任意成员变更后，组织内 `ACTIVE OWNER` 数量始终 >= 1。
3. 自降权/自禁用等危险自操作被稳定拒绝并返回明确错误码。
4. 成员模型支持 `functional_role_id` 且保证单成员单职能绑定。
5. 新增职能角色接口（查询/创建/启停用）可用。
6. 成员禁用后，关联 API key 与会话联动失效符合策略。

### 1.4 Phase 5 功能（v0.4.0 新增）

1. AC-BE-501：`GET /api/auth/context` 可返回 `user/activeOrg/availableOrgs/scopeMode`。
2. AC-BE-502：`POST /api/admin/users` 在 `orgId` 缺省时默认使用 `current_user.org_id`。
3. AC-BE-503：`POST /api/admin/users` 在跨组织 `orgId` 传入时稳定返回 `PERMISSION_DENIED`。
4. AC-BE-504：当前用户无组织上下文时，管理写接口返回 `NO_ACTIVE_ORG`。
5. AC-BE-505：`NO_ACTIVE_ORG` 与跨组织拒绝均写入审计日志（`result=FAILED`）。
6. AC-BE-506：`scopeMode` 当前固定 `ORG_SCOPED`，契约字段稳定可解析。

### 1.5 Phase 6 功能（v0.5.0 新增）

1. AC-BE-601：`GET /api/admin/member-options` 可按 `orgId+query(prefix)` 返回成员候选。
2. AC-BE-602：成员检索接口仅返回当前可管理组织数据，不会泄露跨组织成员。
3. AC-BE-603：`POST /api/admin/api-keys` 支持 `orgId?` 且跨组织组合稳定拒绝。
4. AC-BE-604：签发目标成员不存在或不在目标组织时返回 `RESOURCE_NOT_FOUND`。
5. AC-BE-605：`GET /api/admin/api-keys` 响应可包含 `userEmail/userDisplayName` 可读字段。
6. AC-BE-606：Phase 6 新增路径的拒绝分支都写入 `FAILED` 审计日志。

## 2. 契约对齐检查

1. `05_backend_contract.md` 中路由、方法、字段与实现一致。
2. 认证响应字段使用 camelCase，与前端契约一致。
3. 错误体结构统一：`detail.error_code + message`。
4. 枚举值与文档一致，无隐式别名。
5. 端点级权限矩阵与文档一致（含 `MEMBER` 本人数据限制）。
6. 成员语义接口（`/api/admin/members/*`）与兼容接口（`/api/admin/users/*`）行为一致。
7. 职能角色字段语义与约束（单值绑定）与契约一致。
8. `GET /api/admin/member-options` 与 `POST /api/admin/api-keys` 的组织校验语义一致。

## 3. 持久化与流程检查

1. 新增表与索引已迁移成功。
2. 历史数据回填脚本可执行且结果可验证。
3. API Key 仅存 hash，不存明文。
4. Refresh token 可被吊销，吊销后不可再次刷新。
5. 业务查询默认按组织隔离，管理员策略按设计放宽。
6. `VIEWER` 仅可读，写接口调用返回 `PERMISSION_DENIED`。
7. 历史数据回填后 `org_id/created_by_user_id` 空值数量为 0。

## 4. 错误与可观测性检查

1. `AUTH_ERROR/TOKEN_EXPIRED/PERMISSION_DENIED` 返回状态码正确。
2. `USER_DISABLED/API_KEY_REVOKED` 场景可稳定复现。
3. 审计日志包含 actor、action、target、timestamp。
4. 认证失败与权限失败均有结构化日志字段（`user_id/org_id/request_id`）。
5. 登录接口限流配置在 Phase 3 可启用并可观测。
6. refresh token 重放会被拦截并产生审计/指标记录。
7. 灰度期 `auth_legacy_fallback_total` 指标可用且可下钻排查。
8. 治理拒绝类错误（`LAST_OWNER_PROTECTED` 等）具备稳定状态码与审计记录。
9. `NO_ACTIVE_ORG` 错误码在契约、实现、日志中一致。
10. 成员检索接口具备查询长度与 limit 上限保护，避免无界扫描。

## 5. 追踪映射（v0.5.0 增量）

| 验收项 | 关联任务 | 关联契约 |
|---|---|---|
| AC-BE-501 | BE-5.1 | BC-401 |
| AC-BE-502 | BE-5.2 | BC-402 |
| AC-BE-503 | BE-5.2 | BC-402 |
| AC-BE-504 | BE-5.3 | BC-403 |
| AC-BE-505 | BE-5.3 | BC-403 |
| AC-BE-506 | BE-5.4 | BC-401 |
| AC-BE-601 | BE-6.1/BE-6.2 | BC-501 |
| AC-BE-602 | BE-6.1/BE-6.2 | BC-501 |
| AC-BE-603 | BE-6.3 | BC-502 |
| AC-BE-604 | BE-6.3/BE-6.5 | BC-502 |
| AC-BE-605 | BE-6.4 | BC-503 |
| AC-BE-606 | BE-6.5/BE-6.6 | BC-501/BC-502/BC-503 |
