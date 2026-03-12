# 前端契约文档 - user_management
> Version: v0.5.0
> Last Updated: 2026-03-12
> Status: Draft

> Contract Priority (v0.5.0): 若旧段落与 `v0.5.0` 新增规则冲突，以 `v0.5.0` 为准；`v0.4.0` 作为兼容基线保留。

## 1. 请求模型（前端视角）

### 1.1 认证接口请求

1. `POST /api/auth/key-login`

```ts
type KeyLoginRequest = {
  apiKey: string;
  deviceInfo?: string;
};
```

2. `POST /api/auth/refresh`

```ts
type RefreshTokenRequest = {
  refreshToken: string;
};
```

3. `POST /api/auth/logout`

```ts
type LogoutRequest = {
  refreshToken?: string;
  allDevices?: boolean;
};
```

4. `GET /api/auth/me`

- 无请求体。

5. `GET /api/auth/context`（v0.4.0 新增）

- 无请求体。

> Obsolete in v0.2.0: `RefreshTokenRequest` 与 `LogoutRequest.refreshToken` 的请求体 token 传输不再作为主路径。

v0.2.0 生效规则：

1. `POST /api/auth/refresh`：无请求体，使用 Cookie `refresh_token` + Header `X-CSRF-Token`。
2. `POST /api/auth/logout`：请求体仅保留 `allDevices?: boolean`。

```ts
type RefreshRequest = Record<string, never>;

type LogoutRequestV2 = {
  allDevices?: boolean;
};
```

### 1.2 管理接口请求（Phase 2）

1. `POST /api/admin/users`

```ts
type CreateUserRequest = {
  email: string;
  displayName: string;
  role: Role;
  orgId?: string;
};
```

> Obsolete in v0.4.0: 前端“手工输入 `orgId`”交互已废弃，`orgId` 仅允许来自 `AuthContext.availableOrgs` 下拉选项。

v0.4.0 生效规则：

1. `ORG_SCOPED` 下前端默认使用 `activeOrg.id`，不允许用户自由编辑组织 ID。
2. `USER_SCOPED`（未来）允许选择 `availableOrgs` 中的组织后提交。
3. 若 `activeOrg` 为空，前端必须阻断创建并提示“当前账号无可用组织”。

2. `GET /api/admin/users`

```ts
type ListUsersQuery = {
  query?: string;
  role?: Role;
  status?: UserStatus;
  page?: number;
  pageSize?: number;
};
```

3. `PATCH /api/admin/users/{user_id}/status`

```ts
type UpdateUserStatusRequest = {
  status: UserStatus;
};
```

4. `PATCH /api/admin/users/{user_id}/role`

```ts
type UpdateUserRoleRequest = {
  role: Role;
};
```

5. `POST /api/admin/api-keys`

```ts
type IssueApiKeyRequest = {
  userId: string;
  name: string;
  expiresAt?: string; // ISO 8601
  orgId?: string; // v0.5.0：可选，ORG_SCOPED 下由上下文固定
};
```

6. `GET /api/admin/api-keys`

```ts
type ListApiKeysQuery = {
  userId?: string;
  orgId?: string; // v0.5.0：可选，未来 USER_SCOPED 支持按组织过滤
  status?: ApiKeyStatus;
  page?: number;
  pageSize?: number;
};
```

7. `POST /api/admin/api-keys/{key_id}/revoke`

- 无请求体。

8. `GET /api/admin/member-options`（v0.5.0 新增）

```ts
type ListMemberOptionsQuery = {
  query: string; // 前缀匹配，建议最少 2 字符
  orgId?: string;
  limit?: number; // 默认 20，最大 50
};
```

> v0.3.0 补充（对已有接口的增量约束）：
1. `POST /api/admin/users` 中 `orgId` 不传时，后端默认使用当前登录用户所属组织。
2. `PATCH /api/admin/users/{user_id}/status|role` 进入治理红线校验（如“至少一个 owner”）。
3. 前端在兼容窗口中保留对 `/api/admin/users/*` 的消费能力。

> Obsolete in v0.5.0: API Key 签发流程中“手工输入 userId 文本框”被标记为过时交互，前端主路径改为成员联想选择。

v0.5.0 生效规则（API Key 签发）：

1. 前端提交 `IssueApiKeyRequest.userId` 必须来自成员候选项选择，而非任意文本。
2. `ORG_SCOPED` 下 `orgId` 由 `activeOrg` 固定，不允许自由编辑。
3. `USER_SCOPED`（未来）允许在 `availableOrgs` 中切换组织后再查询成员候选。

### 1.2A 管理接口请求（Phase 4 新增）

1. `GET /api/admin/members`

```ts
type ListMembersQuery = {
  query?: string;
  permissionRole?: Role;
  memberStatus?: MemberStatus;
  functionalRoleId?: string;
  page?: number;
  pageSize?: number;
};
```

2. `PATCH /api/admin/members/{member_id}/role`

```ts
type UpdateMemberRoleRequest = {
  role: Role;
  reason?: string;
};
```

3. `PATCH /api/admin/members/{member_id}/status`

```ts
type UpdateMemberStatusRequest = {
  status: MemberStatus;
  reason?: string;
};
```

4. `PATCH /api/admin/members/{member_id}/functional-role`

```ts
type UpdateMemberFunctionalRoleRequest = {
  functionalRoleId: string;
  reason?: string;
};
```

5. `GET /api/admin/functional-roles`

```ts
type ListFunctionalRolesQuery = {
  isActive?: boolean;
  page?: number;
  pageSize?: number;
};
```

6. `POST /api/admin/functional-roles`

```ts
type CreateFunctionalRoleRequest = {
  code: string;
  name: string;
  description?: string;
};
```

### 1.3 请求头与 Cookie 约定（v0.2.0）

1. 业务与管理接口：
- Header: `Authorization: Bearer <accessToken>`。
2. 刷新与登出：
- Cookie: `refresh_token`（HttpOnly）与 `csrf_token`（非 HttpOnly）。
- Header: `X-CSRF-Token: <csrf_token>`。
3. 所有列表接口统一 query：
- `page`（默认 1）, `pageSize`（默认 20，最大 100）。

### 1.4 既有业务接口请求（鉴权接管）

1. `POST /api/prereview`
2. `GET /api/prereview/{session_id}`
3. `POST /api/prereview/{session_id}/regenerate`
4. `GET /api/prereview/history`
5. `POST /api/files/upload`

说明：

1. 请求体沿用业务域既有契约，不在本文件重复定义字段细节。
2. 统一由 `Authorization: Bearer <accessToken>` 鉴权接管。

## 2. 响应模型（前端视图模型）

### 2.1 认证响应

```ts
type AuthUserView = {
  id: string;
  email: string;
  displayName: string;
  role: Role;
  orgId: string;
  status: UserStatus;
};

type AuthTokenResponse = {
  accessToken: string;
  refreshToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
  user: AuthUserView;
};
```

> Obsolete in v0.2.0: `AuthTokenResponse.refreshToken` 不再保留。

```ts
type AuthTokenResponseV2 = {
  accessToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
  user: AuthUserView;
};

type RefreshResponse = {
  accessToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
};

type LogoutResponse = {
  success: true;
};

type AuthContextOrgView = {
  orgId: string;
  orgName: string;
};

type AuthContextResponse = {
  user: AuthUserView;
  activeOrg: AuthContextOrgView | null;
  availableOrgs: AuthContextOrgView[];
  scopeMode: 'ORG_SCOPED' | 'USER_SCOPED';
};
```

### 2.2 管理响应（Phase 2）

```ts
type UserListItem = {
  id: string;
  email: string;
  displayName: string;
  role: Role;
  status: UserStatus;
  orgId: string;
  createdAt: string;
  lastLoginAt: string | null;
};

type IssueApiKeyResponse = {
  keyId: string;
  keyPrefix: string;
  plainTextKey: string; // 仅本次返回
  expiresAt: string | null;
};
```

```ts
type ListResponse<T> = {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
};

type ApiKeyListItem = {
  keyId: string;
  userId: string;
  userEmail?: string;
  userDisplayName?: string;
  keyPrefix: string;
  status: ApiKeyStatus;
  name: string;
  expiresAt: string | null;
  lastUsedAt: string | null;
  createdAt: string;
};

type MemberOptionItem = {
  userId: string;
  membershipId: string;
  email: string;
  displayName: string;
  permissionRole: Role;
  memberStatus: MemberStatus;
  orgId: string;
};

type ListUsersResponse = ListResponse<UserListItem>;
type ListApiKeysResponse = ListResponse<ApiKeyListItem>;
type ListMemberOptionsResponse = {
  items: MemberOptionItem[];
};

type OperationSuccessResponse = {
  success: true;
};
```

### 2.4 管理响应（Phase 4 新增）

```ts
type FunctionalRoleView = {
  id: string;
  orgId: string;
  code: string;
  name: string;
  description?: string | null;
  isActive: boolean;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
};

type MemberListItem = {
  membershipId: string;
  userId: string;
  email: string;
  displayName: string;
  permissionRole: Role;
  memberStatus: MemberStatus;
  functionalRoleId: string;
  functionalRoleCode: string;
  functionalRoleName: string;
  orgId: string;
  createdAt: string;
  lastLoginAt: string | null;
};

type ListMembersResponse = ListResponse<MemberListItem>;
type ListFunctionalRolesResponse = ListResponse<FunctionalRoleView>;
```

### 2.3 既有业务接口影响

1. `prereview/history/files` 的请求与响应主体不改。
2. 唯一变化：请求头必须携带 `Authorization: Bearer <accessToken>`。
3. 业务详情响应允许新增可选字段：`createdByUserId`, `orgId`（前端可忽略但需容错）。

## 3. 状态与枚举映射

### 3.1 枚举定义

```ts
type Role = 'OWNER' | 'ADMIN' | 'MEMBER' | 'VIEWER';
type UserStatus = 'ACTIVE' | 'DISABLED' | 'PENDING_INVITE';
type ApiKeyStatus = 'ACTIVE' | 'REVOKED' | 'EXPIRED';
```

### 3.1A 枚举扩展（v0.3.0）

```ts
type AccountStatus = 'ACTIVE' | 'LOCKED' | 'DELETED';
type MemberStatus = 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'REMOVED';
```

### 3.2 UI 映射

1. `Role`：用于权限门禁（按钮可见性与路由可访问性）。
2. `UserStatus.DISABLED`：前端立即退出并提示联系管理员。
3. `PENDING_INVITE`：只允许访问激活流程（Phase 3）。

### 3.3 数据可见性映射（v0.2.0）

1. `OWNER/ADMIN`：历史与详情可见组织内全部数据。
2. `MEMBER`：历史与详情仅可见本人创建数据。
3. `VIEWER`：仅可读，不可触发创建/再生成/上传。

### 3.4 权限边界补充（v0.3.0）

1. `OWNER` 可管理 owner 与组织治理策略。
2. `ADMIN` 仅可管理非 owner 成员，不能调整 owner 角色/状态。
3. 职能角色（如产品经理/运营）不直接决定系统权限，仅用于协作语义。

## 4. 错误码到 UI 行为映射

| 错误码 | HTTP | 前端行为 |
|---|---:|---|
| `AUTH_ERROR` | 401 | 登录失败提示“密钥无效或格式错误” |
| `TOKEN_EXPIRED` | 401 | 自动 refresh，失败则跳转登录 |
| `PERMISSION_DENIED` | 403 | 展示无权限提示页 |
| `USER_DISABLED` | 403 | 清理登录态并弹出禁用提示 |
| `API_KEY_REVOKED` | 401 | 提示“密钥已吊销”，返回登录页 |
| `RATE_LIMITED` | 429 | 显示节流提示，延迟重试 |
| `VALIDATION_ERROR` | 400/422 | 表单字段级错误提示 |
| `RESOURCE_NOT_FOUND` | 404 | 提示资源不存在并回退列表页 |
| `PERSISTENCE_ERROR` | 500 | 展示系统错误并允许重试 |
| `LAST_OWNER_PROTECTED` | 409 | 提示“组织至少保留一个可用 owner” |
| `SELF_OPERATION_FORBIDDEN` | 403 | 提示“不允许对当前账号执行该敏感操作” |
| `OWNER_GUARD_VIOLATION` | 403 | 提示“当前角色不可操作 owner 成员” |
| `FUNCTION_ROLE_MISMATCH` | 422 | 提示“职能角色与组织不匹配” |
| `NO_ACTIVE_ORG` | 403 | 提示“当前账号无可用组织，请联系管理员” |

## 5. 与后端契约对齐说明

1. 路由与方法对齐：以 `05_backend_contract.md` 为唯一后端事实来源。
2. 枚举值大小写必须完全一致：`OWNER/ADMIN/MEMBER/VIEWER` 等。
3. token 响应字段命名采用驼峰（后端同步返回驼峰字段）。
4. 前端对新增字段默认“向后兼容”：未知字段忽略，缺失字段采用安全默认。
5. 兼容窗口内同时支持 `/api/admin/users/*`（旧）与 `/api/admin/members/*`（新）契约。

## 6. v0.4.0 兼容说明（新增）

1. `GET /api/auth/context` 为前端组织上下文唯一事实来源。
2. `CreateUserRequest.orgId` 字段在兼容期保留，但前端不再提供自由文本输入。
3. 未来切换到用户态登录时，前端无需改动创建成员接口结构，仅切换 `scopeMode` 分支行为。

## 7. v0.5.0 兼容说明（新增）

1. API Key 签发保留 `userId` 作为提交主键，但前端 UI 主路径不再暴露自由输入框。
2. 新增 `GET /api/admin/member-options` 作为“签发前成员检索”的唯一接口。
3. `IssueApiKeyRequest.orgId?` 为兼容字段：当前 `ORG_SCOPED` 可不传，未来 `USER_SCOPED` 可显式传入。
4. `GET /api/admin/api-keys` 响应可新增 `userEmail/userDisplayName`，前端需向后兼容缺失场景。

## 8. Contract Item IDs（v0.5.0 增量）

| Contract ID | 说明 | 关联端点/模型 |
|---|---|---|
| FC-401 | 登录上下文响应模型（`activeOrg/availableOrgs/scopeMode`） | `GET /api/auth/context` + `AuthContextResponse` |
| FC-402 | 创建成员组织字段语义（仅允许上下文来源） | `POST /api/admin/users` + `CreateUserRequest.orgId?` |
| FC-403 | 无组织上下文错误处理 | `NO_ACTIVE_ORG` 错误码映射 |
| FC-501 | API Key 签发成员检索契约 | `GET /api/admin/member-options` + `ListMemberOptionsResponse` |
| FC-502 | API Key 签发组织语义约束 | `POST /api/admin/api-keys` + `IssueApiKeyRequest.orgId?` |
| FC-503 | API Key 列表可读字段扩展 | `GET /api/admin/api-keys` + `ApiKeyListItem.userEmail/userDisplayName` |
