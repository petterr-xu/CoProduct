# 总体技术设计方案 - user_management
> Version: v0.3.0
> Last Updated: 2026-03-12
> Status: Draft

> Design Priority (v0.3.0): 若旧段落与 v0.3.0 新增规则冲突，以 v0.3.0 为准。

## 1. 背景与目标

当前系统在完成 Phase 1/2 后已具备基础认证与管理能力，但仍存在治理层面的关键缺口：

1. `OWNER/ADMIN` 权限边界不清晰，治理风险仍高。
2. 缺少“危险操作红线”约束（如自降权、自禁用、组织无 owner）。
3. 用户建模仍偏粗糙，未清晰拆分“全局身份”与“组织内身份”。
4. 缺少成员“职能角色”（如产品经理、运营）建模，不利于团队协作与审计。

本版本目标：

1. 建立清晰且可扩展的身份域建模：`UserAccount` + `OrgMembership`。
2. 固化权限红线与组织治理规则，避免管理员误操作导致系统失管。
3. 新增“职能角色（Functional Role）”模型，约束一个成员仅绑定一个职能角色。
4. 在兼容现有接口的前提下，明确后续成员管理 API 的演进方向。

## 2. 范围（In/Out）

### 2.1 In Scope（v0.3.0 新增）

1. 身份模型细化：
- 全局身份：`users`（账号维度，跨组织唯一）。
- 组织内身份：`memberships`（组织维度，承载权限角色与成员状态）。
2. 权限模型细化：
- 明确 `OWNER` 与 `ADMIN` 的差异化边界。
- 增加治理红线约束与失败审计。
3. 职能角色模型：
- 新增 `org_function_roles`。
- `memberships.functional_role_id` 单值绑定（每个成员仅一个职能角色）。
4. 管理 API 演进：
- 在保留 `/api/admin/users/*` 兼容路径下，逐步引入 `/api/admin/members/*` 语义。

### 2.2 Out of Scope（本轮不做）

1. 企业级 SSO（OIDC/SAML）完整接入。
2. 多组织切换 UI 与跨组织委派管理。
3. 细粒度 ABAC 策略编辑器与工作流审批。

## 3. 总体架构与关键流程

### 3.1 架构摘要

1. 认证域：`auth api + auth service + token provider + session repository`。
2. 身份域：`users + memberships + org_function_roles`。
3. 治理域：`admin member/key/audit APIs + policy guard`。
4. 前端分层：认证状态层、权限门禁层、管理端领域层（成员/职能/密钥/审计）。

```mermaid
flowchart LR
    UI[Frontend] --> Login[Auth APIs]
    Login --> AuthSvc[AuthService]
    AuthSvc --> IdentityRepo[User/Membership Repository]
    AuthSvc --> SessionRepo[AuthSession Repository]
    AuthSvc --> JWT[TokenProvider]

    UI --> BizAPI[Business APIs]
    BizAPI --> Guard[get_current_user]
    Guard --> Policy[Permission Policy Guard]
    Policy --> IdentityRepo

    UI --> AdminAPI[Admin APIs]
    AdminAPI --> AdminSvc[AdminMemberService]
    AdminSvc --> IdentityRepo
    AdminSvc --> FuncRepo[FunctionRole Repository]
    AdminSvc --> KeyRepo[ApiKey Repository]
    AdminSvc --> AuditRepo[Audit Repository]
```

### 3.2 关键链路

1. 登录链路：
- API Key 鉴权通过后，解析到 `user + membership`，签发 access/refresh token。
2. 鉴权链路：
- token 解码后以服务端 membership 为准，动态覆盖 token 中的旧 role。
3. 管理链路：
- 成员管理操作先过权限判定，再过“治理红线”判定，最后写审计。
4. 职能链路：
- 成员创建/更新必须绑定单一职能角色（可使用默认 `unassigned`）。

## 4. 数据与状态模型

### 4.1 身份模型分层（v0.3.0）

1. `UserAccount`（全局身份）
- 语义：用户是谁（跨组织唯一）。
- 建议字段：`id/email/display_name/account_status/created_at/disabled_at`。
2. `OrgMembership`（组织内身份）
- 语义：用户在某组织内是谁（权限、职能、成员状态）。
- 建议字段：`id/user_id/org_id/permission_role/functional_role_id/member_status`。
3. `OrgFunctionalRole`（组织职能角色）
- 语义：组织内职能字典。
- 建议字段：`id/org_id/code/name/description/is_active/sort_order`。

> Obsolete in v0.3.0: 旧版将“用户状态 + 组织成员状态”混合表达，语义不清。

### 4.2 状态模型（v0.3.0）

1. 账号状态（`users.account_status`）：`ACTIVE | LOCKED | DELETED`
2. 成员状态（`memberships.member_status`）：`INVITED | ACTIVE | SUSPENDED | REMOVED`
3. API Key 状态：`ACTIVE | REVOKED | EXPIRED`
4. Auth Session 状态：`ACTIVE | REVOKED | EXPIRED`

### 4.3 权限角色与职能角色

1. 权限角色（`permission_role`）决定可执行操作：`OWNER | ADMIN | MEMBER | VIEWER`
2. 职能角色（`functional_role`）仅用于团队职能表达，不直接决定系统权限。
3. 单成员单职能约束：一个 membership 只能绑定一个 `functional_role_id`。

### 4.4 权限边界（v0.3.0）

| 能力 | OWNER | ADMIN | MEMBER | VIEWER |
|---|---|---|---|---|
| 组织治理（owner 交接/关键安全策略） | ✅ | ❌ | ❌ | ❌ |
| 管理 OWNER 成员 | ✅ | ❌ | ❌ | ❌ |
| 管理 ADMIN/MEMBER/VIEWER | ✅ | ✅ | ❌ | ❌ |
| 业务写（预审/再生成/上传） | ✅ | ✅ | ✅(本人数据) | ❌ |
| 业务读（历史/详情） | ✅(组织全量) | ✅(组织全量) | ✅(本人数据) | ✅(组织只读) |

### 4.5 治理红线（v0.3.0）

1. 组织必须始终至少有一个 `ACTIVE OWNER`。
2. `ADMIN` 不能修改任何 `OWNER` 的角色/状态。
3. `OWNER` 不能直接把自己降为非 owner 或禁用自己（需先完成 owner 交接）。
4. 禁用成员时，必须联动失效其 active sessions 与 active API keys。
5. 所有拒绝类高风险操作也必须写入审计日志。

## 5. 接口演进策略

### 5.1 兼容原则

1. 现有 `/api/admin/users/*` 在兼容窗口保留。
2. 新语义优先：逐步迁移到 `/api/admin/members/*`。
3. 字段演进采用“新增优先、保留旧字段”策略，避免破坏前端。

### 5.2 新增接口方向（规划）

1. `GET /api/admin/functional-roles`
2. `POST /api/admin/functional-roles`
3. `PATCH /api/admin/members/{member_id}/functional-role`

## 6. 阶段规划（Phase 1..N）

### Phase 1（已完成）

1. 新增用户/组织/密钥/会话/审计表与迁移。
2. 认证接口与业务鉴权接管。

### Phase 2（已完成）

1. 管理员 API（用户/密钥/审计）与最小管理页面。

### Phase 3（在研）

1. 安全增强（邀请、限流、会话安全）。

### Phase 4（v0.3.0 新增）

1. 身份模型细化（全局身份 vs 组织内身份）。
2. 权限红线治理规则落地（至少一个 owner、禁止危险自操作）。
3. 职能角色模型与成员单职能约束落地。
4. 管理 API 语义升级（users -> members，保留兼容层）。

## 7. 风险与缓解

### 7.1 主要风险（新增）

1. 风险：权限边界调整导致旧前端行为与后端策略冲突。
- 缓解：后端返回明确错误码与可操作原因，前端按策略禁用按钮。
2. 风险：模型迁移阶段出现 membership 与 functional role 不一致。
- 缓解：迁移分步执行，先补默认 `unassigned` 职能后再加非空约束。
3. 风险：治理红线引入后出现“无法执行管理操作”的运营阻塞。
- 缓解：提供 owner 交接流程与 break-glass 操作手册（审计留痕）。

### 7.2 回滚策略

1. 接口层回滚：保留 `/api/admin/users/*` 兼容路径作为短期退路。
2. 数据层回滚：不回滚核心身份字段，仅允许脚本修复脏数据。
3. 策略层回滚：红线策略可配置降级，但降级必须记录审计事件。
