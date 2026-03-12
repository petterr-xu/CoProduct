# 后端契约文档 - user_management
> Version: v0.2.0
> Last Updated: 2026-03-12
> Status: Draft

> Contract Priority (v0.2.0): 若旧段落与 `Obsolete in v0.2.0` 后的新规则冲突，以新规则为准。

## 1. API 列表（Method + Path）

### 1.1 认证域（Phase 1）

1. `POST /api/auth/key-login`
2. `POST /api/auth/refresh`
3. `POST /api/auth/logout`
4. `GET /api/auth/me`

### 1.2 管理域（Phase 2）

1. `GET /api/admin/users`
2. `POST /api/admin/users`
3. `PATCH /api/admin/users/{user_id}/status`
4. `PATCH /api/admin/users/{user_id}/role`
5. `POST /api/admin/api-keys`
6. `GET /api/admin/api-keys`
7. `POST /api/admin/api-keys/{key_id}/revoke`

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
  "name": "team-laptop",
  "expiresAt": "2026-06-01T00:00:00Z"
}
```

6. `GET /api/admin/api-keys`
- Query: `userId?: string`, `status?: ApiKeyStatus`, `page?: number=1`, `pageSize?: number=20(max 100)`。
7. `POST /api/admin/api-keys/{key_id}/revoke`
- 请求体：空对象 `{}`。

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
| `POST /api/prereview/{id}/regenerate` | ✅ | ✅ | ✅(本人数据) | ❌ |
| `GET /api/prereview/{id}` | ✅ | ✅ | ✅(本人数据) | ✅ |
| `GET /api/prereview/history` | ✅ | ✅ | ✅(本人数据) | ✅ |
| `POST /api/files/upload` | ✅ | ✅ | ✅ | ❌ |
| `GET/POST/PATCH /api/admin/*` | ✅ | ✅ | ❌ | ❌ |

数据范围规则：

1. 所有查询先按 `orgId` 过滤。
2. `MEMBER` 仅能访问 `createdByUserId == self` 的业务数据。
3. `VIEWER` 只读，禁止所有写接口。

## 5. 与前端契约对齐说明

1. 与 `04_frontend_contract.md` 路径、字段名、枚举值逐项对齐。
2. 响应字段统一驼峰命名（camelCase），避免前端二次映射成本。
3. 保留既有业务接口 body，不做破坏性改动，仅升级鉴权机制。
4. 新增业务字段（`orgId/createdByUserId`）应为可选，避免旧前端解析失败。
