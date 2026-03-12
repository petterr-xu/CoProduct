# 后端契约文档 - user_management
> Version: v0.5.0
> Last Updated: 2026-03-12
> Status: Draft

> Contract Priority (v0.5.0): 保留 `v0.4.0` 既有接口契约作为兼容基线；`v0.5.0` 新增段落定义演进后规则。

## 1. API 列表（Method + Path）

### 1.1 认证域（Phase 1）

1. `POST /api/auth/key-login`
2. `POST /api/auth/refresh`
3. `POST /api/auth/logout`
4. `GET /api/auth/me`
5. `GET /api/auth/context`（v0.4.0 新增）

### 1.2 管理域（Phase 2）

1. `GET /api/admin/users`
2. `POST /api/admin/users`
3. `PATCH /api/admin/users/{user_id}/status`
4. `PATCH /api/admin/users/{user_id}/role`
5. `POST /api/admin/api-keys`
6. `GET /api/admin/api-keys`
7. `POST /api/admin/api-keys/{key_id}/revoke`
8. `GET /api/admin/member-options`（v0.5.0 新增）

### 1.2A 管理域（v0.3.0 对已有接口的补充约束）

对以下已有接口补充治理规则，不删除既有契约：

1. `POST /api/admin/users`
2. `PATCH /api/admin/users/{user_id}/status`
3. `PATCH /api/admin/users/{user_id}/role`

补充规则：

1. `orgId` 省略时，默认使用当前登录成员所属组织。
2. 角色/状态变更必须满足“至少一个 active owner”约束。
3. `ADMIN` 不允许操作 `OWNER` 目标成员。
4. 禁止危险自操作（自降权/自禁用）并返回明确错误码。

### 1.2B 管理域（Phase 4 新增）

1. `GET /api/admin/members`
2. `PATCH /api/admin/members/{member_id}/role`
3. `PATCH /api/admin/members/{member_id}/status`
4. `PATCH /api/admin/members/{member_id}/functional-role`
5. `GET /api/admin/functional-roles`
6. `POST /api/admin/functional-roles`

### 1.3 既有业务域（接入新鉴权）

1. `POST /api/prereview`
2. `GET /api/prereview/{session_id}`
3. `POST /api/prereview/{session_id}/regenerate`
4. `GET /api/prereview/history`
5. `POST /api/files/upload`

以上接口从静态 token 校验迁移为 `Bearer access_token` 校验。

## 2. 请求结构与校验规则

### 2.1 `POST /api/auth/key-login`

请求体：

```json
{
  "apiKey": "cpk_live_xxx",
  "deviceInfo": "macOS-chrome"
}
```

校验：

1. `apiKey` 必填，长度 20~128。
2. key 前缀必须匹配系统支持规则（如 `cpk_`）。
3. key 必须处于 `ACTIVE` 且未过期。
4. 对同一 IP/前缀做限流（Phase 3 强制）。

### 2.2 `POST /api/auth/refresh`

```json
{ "refreshToken": "..." }
```

校验：

1. `refreshToken` 必填。
2. refresh token 签名有效且未过期。
3. 对应会话状态为 `ACTIVE`。

### 2.3 `POST /api/auth/logout`

```json
{ "refreshToken": "...", "allDevices": false }
```

校验：

1. 二选一：提供 refresh token 或使用当前 access token 绑定会话。
2. `allDevices=true` 仅允许当前用户操作自己会话；管理员可扩展全量吊销能力。

> Obsolete in v0.2.0: 上述 refresh/logout 请求体 token 方案不再作为默认实现。

v0.2.0 生效规则：

1. `POST /api/auth/refresh`：
- 请求体：空对象 `{}`。
- Cookie：必须携带 `refresh_token`。
- Header：必须携带 `X-CSRF-Token` 且与 `csrf_token` cookie 一致。
2. `POST /api/auth/logout`：
- 请求体仅允许 `{ "allDevices": boolean }`。
- 当前设备登出通过 `refresh_token` cookie 定位会话。

### 2.4 管理接口请求（Phase 2）

1. 创建用户：`email/displayName/role` 必填。
2. 更新状态：`status in [ACTIVE, DISABLED, PENDING_INVITE]`。
3. 更新角色：`role in [OWNER, ADMIN, MEMBER, VIEWER]`。
4. 签发密钥：`userId/name` 必填；`expiresAt` 可选 ISO 时间。
5. v0.5.0：签发密钥新增 `orgId?` 兼容字段；成员检索通过 `GET /api/admin/member-options` 提供候选。

### 2.4A `GET /api/auth/context`（v0.4.0 新增）

请求体：无。

校验：

1. 必须已通过 `Authorization: Bearer <accessToken>` 鉴权。
2. 基于当前会话加载用户与组织上下文。
3. 若当前用户没有可用组织，`activeOrg` 返回 `null`，并允许业务接口按策略返回 `NO_ACTIVE_ORG`。

### 2.5 管理接口请求细化（v0.2.0）

1. `GET /api/admin/users`
- Query: `query?: string`, `role?: Role`, `status?: UserStatus`, `page?: number=1`, `pageSize?: number=20(max 100)`。
2. `POST /api/admin/users`

```json
{
  "email": "member@coproduct.dev",
  "displayName": "Member A",
  "role": "MEMBER",
  "orgId": "org_default"
}
```

> Obsolete in v0.4.0: `orgId` 自由输入语义废弃，仅保留兼容字段。

v0.4.0 生效规则：

1. `orgId` 缺省：默认使用 `current_user.org_id`。
2. `orgId` 传入且不等于 `current_user.org_id`：返回 `403 PERMISSION_DENIED`。
3. `current_user.org_id` 为空：返回 `403 NO_ACTIVE_ORG`。

3. `PATCH /api/admin/users/{user_id}/status`

```json
{ "status": "DISABLED" }
```

4. `PATCH /api/admin/users/{user_id}/role`

```json
{ "role": "VIEWER" }
```

5. `POST /api/admin/api-keys`

```json
{
  "userId": "usr_xxx",
  "orgId": "org_default",
  "name": "team-laptop",
  "expiresAt": "2026-06-01T00:00:00Z"
}
```

`orgId` 字段语义（v0.5.0）：

1. 兼容可选字段；缺省时默认 `current_user.org_id`。
2. 在 `ORG_SCOPED` 下若传入且不等于 `current_user.org_id`，返回 `403 PERMISSION_DENIED`。
3. 在未来 `USER_SCOPED` 下，`orgId` 必须属于 `availableOrgs` 且目标成员在该组织存在 membership。

6. `GET /api/admin/api-keys`
- Query: `userId?: string`, `orgId?: string`, `status?: ApiKeyStatus`, `page?: number=1`, `pageSize?: number=20(max 100)`。
7. `POST /api/admin/api-keys/{key_id}/revoke`
- 请求体：空对象 `{}`。

8. `GET /api/admin/member-options`（v0.5.0 新增）
- Query: `query: string(>=2)`, `orgId?: string`, `limit?: number=20(max 50)`。
- 语义：仅返回当前可管理组织内、可签发目标的成员候选。
- 匹配：邮箱与显示名前缀匹配（prefix search）。

### 2.6 管理接口请求细化（v0.3.0 新增）

1. `GET /api/admin/members`
- Query: `query?: string`, `permissionRole?: Role`, `memberStatus?: MemberStatus`, `functionalRoleId?: string`, `page?: number=1`, `pageSize?: number=20(max 100)`。

2. `PATCH /api/admin/members/{member_id}/role`

```json
{ "role": "ADMIN", "reason": "owner handover completed" }
```

3. `PATCH /api/admin/members/{member_id}/status`

```json
{ "status": "SUSPENDED", "reason": "security review" }
```

4. `PATCH /api/admin/members/{member_id}/functional-role`

```json
{ "functionalRoleId": "frl_xxx", "reason": "team reassignment" }
```

5. `POST /api/admin/functional-roles`

```json
{
  "code": "pm",
  "name": "产品经理",
  "description": "负责需求设计与协同"
}
```

## 3. 响应结构与字段语义

### 3.1 `POST /api/auth/key-login` 成功响应

```json
{
  "accessToken": "...",
  "refreshToken": "...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": {
    "id": "usr_xxx",
    "email": "member@coproduct.dev",
    "displayName": "Member A",
    "role": "MEMBER",
    "orgId": "org_default",
    "status": "ACTIVE"
  }
}
```

字段语义：

1. `accessToken`：短期业务访问令牌。
2. `refreshToken`：刷新令牌，轮换策略由服务端控制。
3. `tokenType`：固定 `Bearer`。
4. `expiresIn`：Access Token 剩余秒数。
5. `user`：当前用户上下文，用于前端权限渲染。

> Obsolete in v0.2.0: 登录响应体中的 `refreshToken` 字段不再返回。

v0.2.0 登录响应：

```json
{
  "accessToken": "...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": {
    "id": "usr_xxx",
    "email": "member@coproduct.dev",
    "displayName": "Member A",
    "role": "MEMBER",
    "orgId": "org_default",
    "status": "ACTIVE"
  }
}
```

同时响应头设置：

1. `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Path=/api/auth`
2. `Set-Cookie: csrf_token=...; Secure; SameSite=Lax; Path=/api/auth`

### 3.2 `GET /api/auth/me` 成功响应

```json
{
  "id": "usr_xxx",
  "email": "member@coproduct.dev",
  "displayName": "Member A",
  "role": "MEMBER",
  "orgId": "org_default",
  "status": "ACTIVE"
}
```

### 3.2A `GET /api/auth/context` 成功响应（v0.4.0 新增）

```json
{
  "user": {
    "id": "usr_xxx",
    "email": "member@coproduct.dev",
    "displayName": "Member A",
    "role": "MEMBER",
    "orgId": "org_default",
    "status": "ACTIVE"
  },
  "activeOrg": {
    "orgId": "org_default",
    "orgName": "Default Organization"
  },
  "availableOrgs": [
    {
      "orgId": "org_default",
      "orgName": "Default Organization"
    }
  ],
  "scopeMode": "ORG_SCOPED"
}
```

字段语义：

1. `activeOrg`：当前会话默认生效组织，可为 `null`。
2. `availableOrgs`：当前用户可见组织列表。
3. `scopeMode`：上下文作用域模式，当前阶段为 `ORG_SCOPED`，未来可扩展 `USER_SCOPED`。

### 3.3 `POST /api/auth/refresh` 成功响应（v0.2.0）

```json
{
  "accessToken": "...",
  "tokenType": "Bearer",
  "expiresIn": 3600
}
```

### 3.4 `POST /api/auth/logout` 成功响应（v0.2.0）

```json
{
  "success": true
}
```

并清空 `refresh_token` 与 `csrf_token` cookies。

### 3.5 管理接口关键响应（Phase 2）

1. 创建用户返回 `UserListItem`。
2. 签发密钥返回：

```json
{
  "keyId": "key_xxx",
  "keyPrefix": "cpk_live_12ab",
  "plainTextKey": "cpk_live_12ab....",
  "expiresAt": "2026-06-01T00:00:00Z"
}
```

`plainTextKey` 仅在签发时返回一次，后续查询不再返回。

`GET /api/admin/users` 响应：

```json
{
  "items": [
    {
      "id": "usr_xxx",
      "email": "member@coproduct.dev",
      "displayName": "Member A",
      "role": "MEMBER",
      "status": "ACTIVE",
      "orgId": "org_default",
      "createdAt": "2026-03-12T01:00:00Z",
      "lastLoginAt": "2026-03-12T02:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

`GET /api/admin/api-keys` 响应：

```json
{
  "items": [
    {
      "keyId": "key_xxx",
      "userId": "usr_xxx",
      "userEmail": "member@coproduct.dev",
      "userDisplayName": "Member A",
      "keyPrefix": "cpk_live_12ab",
      "status": "ACTIVE",
      "name": "team-laptop",
      "expiresAt": "2026-06-01T00:00:00Z",
      "lastUsedAt": null,
      "createdAt": "2026-03-12T01:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

`GET /api/admin/member-options` 响应（v0.5.0 新增）：

```json
{
  "items": [
    {
      "userId": "usr_xxx",
      "membershipId": "mem_xxx",
      "email": "member@coproduct.dev",
      "displayName": "Member A",
      "permissionRole": "MEMBER",
      "memberStatus": "ACTIVE",
      "orgId": "org_default"
    }
  ]
}
```

### 3.6 管理接口关键响应（v0.3.0 新增）

`GET /api/admin/members` 响应：

```json
{
  "items": [
    {
      "membershipId": "mem_xxx",
      "userId": "usr_xxx",
      "email": "member@coproduct.dev",
      "displayName": "Member A",
      "permissionRole": "MEMBER",
      "memberStatus": "ACTIVE",
      "functionalRoleId": "frl_xxx",
      "functionalRoleCode": "pm",
      "functionalRoleName": "产品经理",
      "orgId": "org_default",
      "createdAt": "2026-03-12T01:00:00Z",
      "lastLoginAt": "2026-03-12T02:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

`GET /api/admin/functional-roles` 响应：

```json
{
  "items": [
    {
      "id": "frl_xxx",
      "orgId": "org_default",
      "code": "pm",
      "name": "产品经理",
      "description": "负责需求设计与协同",
      "isActive": true,
      "sortOrder": 10,
      "createdAt": "2026-03-12T01:00:00Z",
      "updatedAt": "2026-03-12T01:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

## 4. 状态/错误码规则

### 4.1 HTTP 状态码

1. `200`：查询、刷新、登出。
2. `201`：创建用户、签发密钥。
3. `400/422`：参数校验失败。
4. `401`：鉴权失败。
5. `403`：鉴权通过但无权限。
6. `404`：资源不存在。
7. `429`：限流。
8. `500`：服务内部错误。

### 4.2 错误码

1. `AUTH_ERROR`
2. `TOKEN_EXPIRED`
3. `PERMISSION_DENIED`
4. `USER_DISABLED`
5. `API_KEY_REVOKED`
6. `RATE_LIMITED`
7. `VALIDATION_ERROR`
8. `PERSISTENCE_ERROR`
9. `RESOURCE_NOT_FOUND`
10. `LAST_OWNER_PROTECTED`
11. `SELF_OPERATION_FORBIDDEN`
12. `OWNER_GUARD_VIOLATION`
13. `FUNCTION_ROLE_MISMATCH`
14. `NO_ACTIVE_ORG`

统一错误体：

```json
{
  "detail": {
    "error_code": "AUTH_ERROR",
    "message": "Invalid API key"
  }
}
```

### 4.3 权限矩阵与数据范围（v0.2.0）

| 接口 | OWNER | ADMIN | MEMBER | VIEWER |
|---|---|---|---|---|
| `POST /api/prereview` | ✅ | ✅ | ✅ | ❌ |
| `POST /api/prereview/{session_id}/regenerate` | ✅ | ✅ | ✅(本人数据) | ❌ |
| `GET /api/prereview/{session_id}` | ✅ | ✅ | ✅(本人数据) | ✅ |
| `GET /api/prereview/history` | ✅ | ✅ | ✅(本人数据) | ✅ |
| `POST /api/files/upload` | ✅ | ✅ | ✅ | ❌ |
| 管理域接口（`/api/admin/*`） | ✅ | ✅ | ❌ | ❌ |

数据范围规则：

1. 所有查询先按 `orgId` 过滤。
2. `MEMBER` 仅能访问 `createdByUserId == self` 的业务数据。
3. `VIEWER` 只读，禁止所有写接口。

### 4.4 权限矩阵补充（v0.3.0）

| 接口 | OWNER | ADMIN | MEMBER | VIEWER |
|---|---|---|---|---|
| `GET /api/admin/members` | ✅ | ✅ | ❌ | ❌ |
| `PATCH /api/admin/members/{member_id}/role` | ✅ | ✅(非 owner) | ❌ | ❌ |
| `PATCH /api/admin/members/{member_id}/status` | ✅ | ✅(非 owner) | ❌ | ❌ |
| `PATCH /api/admin/members/{member_id}/functional-role` | ✅ | ✅(非 owner) | ❌ | ❌ |
| `GET/POST /api/admin/functional-roles` | ✅ | ✅ | ❌ | ❌ |

治理红线约束：

1. 组织必须始终保留至少一个 `ACTIVE OWNER`。
2. `ADMIN` 不能修改 `OWNER` 成员。
3. 禁止危险自操作（自降权/自禁用）。

### 4.5 v0.4.0 上下文与组织规则（新增）

| 接口 | 规则 |
|---|---|
| `GET /api/auth/context` | 任意已登录角色可调用；仅返回当前用户可见组织上下文 |
| `POST /api/admin/users` | 组织来源受当前上下文约束；不允许跨组织创建成员 |
| 管理写接口（`/api/admin/*`） | 当 `activeOrg` 缺失时返回 `NO_ACTIVE_ORG`，拒绝写入 |

### 4.6 v0.5.0 API Key 签发可用性与组织规则（新增）

| 接口 | 规则 |
|---|---|
| `GET /api/admin/member-options` | `query` 最小长度 2；返回结果必须属于目标组织上下文 |
| `POST /api/admin/api-keys` | `userId` 目标成员必须在目标组织存在可用 membership；跨组织组合返回 `PERMISSION_DENIED/RESOURCE_NOT_FOUND` |
| `GET /api/admin/api-keys` | 可按 `orgId` 过滤；响应可附带 `userEmail/userDisplayName` 便于管理 |

## 5. 与前端契约对齐说明

1. 与 `04_frontend_contract.md` 路径、字段名、枚举值逐项对齐。
2. 响应字段统一驼峰命名（camelCase），避免前端二次映射成本。
3. 保留既有业务接口 body，不做破坏性改动，仅升级鉴权机制。
4. 新增业务字段（`orgId/createdByUserId`）应为可选，避免旧前端解析失败。
5. 管理接口演进遵循“旧接口保留 + 新接口追加”策略，兼容期允许双路由并存。
6. v0.4.0 新增 `GET /api/auth/context`，与前端 `AuthContextResponse` 字段一一对齐。
7. v0.5.0 新增 `GET /api/admin/member-options`，用于签发前成员检索，避免前端依赖手工 userId 输入。

## 6. Contract Item IDs（v0.5.0 增量）

| Contract ID | 说明 | 关联端点 |
|---|---|---|
| BC-401 | 登录上下文接口契约（`activeOrg/availableOrgs/scopeMode`） | `GET /api/auth/context` |
| BC-402 | 创建成员组织约束契约（`orgId` 兼容字段收敛） | `POST /api/admin/users` |
| BC-403 | 无组织上下文拒绝契约 | 管理写接口 + `NO_ACTIVE_ORG` |
| BC-501 | API Key 目标成员检索契约 | `GET /api/admin/member-options` |
| BC-502 | API Key 签发组织语义契约 | `POST /api/admin/api-keys` + `orgId?` |
| BC-503 | API Key 列表可读字段扩展契约 | `GET /api/admin/api-keys` + `userEmail/userDisplayName` |
